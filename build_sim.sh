if [ -d "build" ]; then rm -Rf build; fi
mkdir -p build
cd build || exit
rm -rf *
cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DPython3_EXECUTABLE=$(which python3) ..
make
cd ..
echo Compilation done. Executable in the bin folder