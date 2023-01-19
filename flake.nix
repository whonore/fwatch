rec {
  description = "A very simple file watcher";

  inputs.nixpkgs.url = "github:nixos/nixpkgs";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.gitignore = {
    url = "github:hercules-ci/gitignore.nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    gitignore,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      inherit (gitignore.lib) gitignoreSource;
      pkgs = nixpkgs.legacyPackages.${system};

      fwatch = pkgs.poetry2nix.mkPoetryApplication {
        projectDir = ./.;
        overrides = pkgs.poetry2nix.overrides.withDefaults (
          self: super: (pkgs.lib.listToAttrs (builtins.map
            (x: {
              name = x;
              value = super."${x}".overridePythonAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or []) ++ [self.setuptools];
              });
            })
            ["bump2version"]))
        );
      };
    in {
      packages.default = fwatch;
    });
}
