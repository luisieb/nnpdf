#!/bin/bash
mkdir build
cd build
cmake ../
make
make install
make wrapper
