{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.pyqt6
    python312Packages.pip
  ];
  
  shellHook = ''
    echo "ALOPEX Development Environment"
    echo "PyQt6 ready for GUI development"
    cd alopex-qt
  '';
}