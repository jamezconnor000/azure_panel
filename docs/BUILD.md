# Build Instructions

## Prerequisites

- CMake 3.10+
- GCC/Clang C compiler
- SQLite3 development files
- Linux or macOS

## Install Dependencies

### Ubuntu/Debian
```bash
sudo apt-get install cmake build-essential sqlite3 libsqlite3-dev
```

### macOS
```bash
brew install cmake sqlite3
```

## Build Steps

```bash
# Clone repository
git clone <url>
cd hal_project

# Create build directory
mkdir build && cd build

# Configure
cmake ..

# Build
make -j$(nproc)

# Test
ctest --output-on-failure

# Install
sudo make install
```

## Build Options

```bash
# Debug build
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release build with optimization
cmake -DCMAKE_BUILD_TYPE=Release ..

# With test coverage
cmake -DCOVERAGE=ON ..
make coverage
```

## Running Examples

After build:

```bash
# Basic access control example
./examples/example_basic

# Event subscription example
./examples/example_events

# Card provisioning example
./examples/example_provision
```

## Python Installation

```bash
pip install -e .
```

Or:

```bash
python setup.py install
```

## Docker Build

```bash
docker build -t hal:latest .
docker run -it hal:latest /bin/bash
```

## Troubleshooting

### CMake not found
```bash
pip install cmake
```

### SQLite3 not found
```bash
# Ubuntu
sudo apt-get install libsqlite3-dev
```

### Build fails
```bash
rm -rf build
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make VERBOSE=1
```
