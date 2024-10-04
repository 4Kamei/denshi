{ pkgs ? import <nixpkgs> {} }:
let
    pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/cf8cc1201be8bc71b7cbbbdaf349b22f4f99c7ae.tar.gz") {};

in pkgs.mkShell {

  nativeBuildInputs = with pkgs.buildPackages; [	
    python312
    python312Packages.pynvim
  ];

  shellHook = ''
    echo "Sourcing sourceme"
    source sourceme
    export PATH="$(pwd)/bin/:$PATH"
    export PYTHONPATH="$(pwd)/cocotb/utils:$PYTHONPATH"
    '';

}
