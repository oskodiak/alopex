/*
 * ALOPEX eBPF Network Security Monitor
 * Kernel-space network monitoring and security controls
 */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define MAX_ENTRIES 4096
#define ALERT_THRESHOLD_NETLINK 10
#define ALERT_THRESHOLD_PRIV_ESC 1
#define TIME_WINDOW_SEC 60

/* Security event types */
enum alopex_event_type {
    ALOPEX_EVENT_NETLINK_ANOMALY = 1,
    ALOPEX_EVENT_PRIV_ESCALATION = 2,
    ALOPEX_EVENT_SUSPICIOUS_NETWORK = 3,
    ALOPEX_EVENT_UNAUTHORIZED_INTERFACE = 4,
    ALOPEX_EVENT_MALICIOUS_PATTERN = 5
};

/* Security event structure */
struct alopex_security_event {
    __u32 pid;
    __u32 uid;
    __u32 gid;
    __u64 timestamp;
    __u32 event_type;
    __u32 severity;
    char comm[16];
    __u32 netlink_type;
    __u32 interface_index;
    __u8 suspicious_pattern[32];
};

/* Maps for tracking security events */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);  /* PID */
    __type(value, struct alopex_security_event);
} alopex_events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);  /* UID */
    __type(value, __u32); /* Event count */
} netlink_rate_limit SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u32);  /* PID */
    __type(value, __u64); /* Last privilege change timestamp */
} privilege_tracking SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} security_alerts SEC(".maps");

/* Helper to get current timestamp */
static __always_inline __u64 get_timestamp(void)
{
    return bpf_ktime_get_ns();
}

/* Helper to check if user is privileged */
static __always_inline bool is_privileged_user(__u32 uid)
{
    return uid == 0 || uid < 1000;  /* root or system users */
}

/* Helper to detect suspicious netlink patterns */
static __always_inline bool is_suspicious_netlink_pattern(struct nlmsghdr *nlh)
{
    if (!nlh)
        return false;
    
    /* Check for known malicious patterns */
    if (nlh->nlmsg_type == RTM_NEWLINK && nlh->nlmsg_len > 8192) {
        return true;  /* Oversized link messages */
    }
    
    if (nlh->nlmsg_type == RTM_SETLINK && (nlh->nlmsg_flags & NLM_F_CREATE)) {
        return true;  /* Suspicious link creation */
    }
    
    /* Check for rapid-fire netlink messages */
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    __u32 *count = bpf_map_lookup_elem(&netlink_rate_limit, &uid);
    if (count) {
        if (*count > ALERT_THRESHOLD_NETLINK) {
            return true;  /* Rate limit exceeded */
        }
        *count += 1;
    } else {
        __u32 new_count = 1;
        bpf_map_update_elem(&netlink_rate_limit, &uid, &new_count, BPF_NOEXIST);
    }
    
    return false;
}

/* Helper to send security alert */
static __always_inline void send_security_alert(struct alopex_security_event *event)
{
    struct alopex_security_event *alert;
    
    alert = bpf_ringbuf_reserve(&security_alerts, sizeof(*alert), 0);
    if (!alert)
        return;
    
    __builtin_memcpy(alert, event, sizeof(*alert));
    bpf_ringbuf_submit(alert, 0);
}

/* 
 * LSM Hook: Monitor privilege escalation attempts
 * Triggers on commit_creds() kernel function
 */
SEC("lsm/cred_prepare")
int alopex_monitor_privilege_escalation(struct linux_binprm *bprm)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    __u64 now = get_timestamp();
    
    /* Check for privilege escalation patterns */
    __u64 *last_change = bpf_map_lookup_elem(&privilege_tracking, &pid);
    if (last_change) {
        __u64 time_diff = now - *last_change;
        /* If privilege changes within 1 second, it's suspicious */
        if (time_diff < 1000000000ULL) {  /* 1 second in nanoseconds */
            struct alopex_security_event event = {0};
            event.pid = pid;
            event.uid = uid;
            event.timestamp = now;
            event.event_type = ALOPEX_EVENT_PRIV_ESCALATION;
            event.severity = 3;  /* High severity */
            
            bpf_get_current_comm(&event.comm, sizeof(event.comm));
            send_security_alert(&event);
        }
    }
    
    /* Update tracking */
    bpf_map_update_elem(&privilege_tracking, &pid, &now, BPF_ANY);
    
    return 0;
}

/*
 * Tracepoint: Monitor netlink socket operations
 * Detects malicious netlink message patterns
 */
SEC("tracepoint/netlink/netlink_extack")
int alopex_monitor_netlink(struct trace_event_raw_netlink_extack *ctx)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    __u64 now = get_timestamp();
    
    /* Basic validation */
    if (!ctx || !ctx->msg)
        return 0;
    
    struct alopex_security_event event = {0};
    event.pid = pid;
    event.uid = uid;
    event.timestamp = now;
    event.event_type = ALOPEX_EVENT_NETLINK_ANOMALY;
    event.severity = 2;  /* Medium severity */
    
    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    
    /* Check for suspicious patterns in netlink message */
    char msg[32] = {0};
    bpf_probe_read_str(&msg, sizeof(msg), ctx->msg);
    
    /* Look for known attack signatures */
    for (int i = 0; i < 24; i++) {
        if (msg[i] == 0)
            break;
        if (msg[i] == '\\' && msg[i+1] == 'x') {
            /* Hex escape sequences - potential injection */
            event.severity = 3;
            __builtin_memcpy(event.suspicious_pattern, &msg[i], 8);
            break;
        }
    }
    
    send_security_alert(&event);
    return 0;
}

/*
 * XDP Program: Network packet filtering
 * Drops malicious network packets at kernel level
 */
SEC("xdp")
int alopex_network_filter(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)eth + sizeof(*eth) > data_end)
        return XDP_PASS;
    
    /* Only process IP packets */
    if (eth->h_proto != __builtin_bswap16(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *ip = (void *)eth + sizeof(*eth);
    if ((void *)ip + sizeof(*ip) > data_end)
        return XDP_PASS;
    
    /* Check for suspicious network patterns */
    
    /* 1. Block packets with suspicious source IPs */
    __u32 src_ip = __builtin_bswap32(ip->saddr);
    if ((src_ip & 0xFF000000) == 0x0A000000 ||  /* 10.x.x.x private */
        (src_ip & 0xFFFF0000) == 0xAC100000 ||  /* 172.16.x.x private */
        (src_ip & 0xFFFF0000) == 0xC0A80000) {  /* 192.168.x.x private */
        
        /* Log suspicious private IP in public interface */
        struct alopex_security_event event = {0};
        event.timestamp = get_timestamp();
        event.event_type = ALOPEX_EVENT_SUSPICIOUS_NETWORK;
        event.severity = 2;
        
        send_security_alert(&event);
    }
    
    /* 2. Monitor TCP packets for port scanning */
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)ip + sizeof(*ip);
        if ((void *)tcp + sizeof(*tcp) > data_end)
            return XDP_PASS;
            
        __u16 dest_port = __builtin_bswap16(tcp->dest);
        
        /* Flag attempts to connect to sensitive ports */
        if (dest_port == 22 || dest_port == 80 || dest_port == 443 || 
            dest_port == 3389 || dest_port == 5432) {
            
            /* Rate limit connection attempts */
            /* This is a simplified check - production would be more sophisticated */
            if (tcp->syn && !tcp->ack) {  /* SYN packet */
                struct alopex_security_event event = {0};
                event.timestamp = get_timestamp();
                event.event_type = ALOPEX_EVENT_SUSPICIOUS_NETWORK;
                event.severity = 1;
                
                send_security_alert(&event);
            }
        }
    }
    
    return XDP_PASS;
}

/*
 * Kprobe: Monitor interface configuration changes
 * Detects unauthorized network interface manipulation
 */
SEC("kprobe/dev_change_flags")
int alopex_monitor_interface_changes(struct pt_regs *ctx)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    
    /* Only monitor unprivileged users */
    if (is_privileged_user(uid))
        return 0;
    
    struct alopex_security_event event = {0};
    event.pid = pid;
    event.uid = uid;
    event.timestamp = get_timestamp();
    event.event_type = ALOPEX_EVENT_UNAUTHORIZED_INTERFACE;
    event.severity = 3;  /* High severity for unprivileged interface changes */
    
    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    send_security_alert(&event);
    
    return 0;
}

/*
 * Fexit program: Monitor network namespace changes
 * Detects container escape attempts
 */
SEC("fexit/copy_net_ns")
int alopex_monitor_netns_changes(struct bpf_iter__ns_common *ctx)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    
    /* Network namespace changes by unprivileged users are suspicious */
    if (!is_privileged_user(uid)) {
        struct alopex_security_event event = {0};
        event.pid = pid;
        event.uid = uid;
        event.timestamp = get_timestamp();
        event.event_type = ALOPEX_EVENT_SUSPICIOUS_NETWORK;
        event.severity = 3;
        
        bpf_get_current_comm(&event.comm, sizeof(event.comm));
        send_security_alert(&event);
    }
    
    return 0;
}

/*
 * Map cleanup function - called periodically
 * Removes old entries to prevent memory leaks
 */
SEC("tp/timer/timer_expire_exit")
int alopex_cleanup_maps(struct trace_event_raw_timer_class *ctx)
{
    __u64 now = get_timestamp();
    __u64 cutoff = now - (TIME_WINDOW_SEC * 1000000000ULL);
    
    /* This is a simplified cleanup - production would iterate through maps */
    /* Cleanup would be handled by userspace control program */
    
    return 0;
}

/* License required for eBPF programs */
char _license[] SEC("license") = "GPL";

/* Program version for compatibility checking */
__u32 _version SEC("version") = 0xFFFFFFFE;