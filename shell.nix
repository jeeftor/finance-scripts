{ pkgs ? import <nixpkgs> { } }:

let
  pythonEnv = pkgs.python312.withPackages (ps: with ps; [
    ps.pip
    ps.numpy
    ps.uv
    # ps.poetry  # Add Poetry here
    # Include any additional Python packages here
  ]);
in
pkgs.mkShell {
  buildInputs = [
    pythonEnv
    pkgs.poetry  # Add Poetry as a top-level attribute

  ];

  shellHook = ''
    export POETRY_HOME=$(pwd)/.poetry
    export PATH=$POETRY_HOME/bin:$PATH
    # Optional: install Poetry if not already installed
    if [ ! -d "$POETRY_HOME" ]; then
      poetry config virtualenvs.in-project true
      poetry install
    fi
    # Activate the Poetry environment
    source .venv/bin/activate
  '';
}