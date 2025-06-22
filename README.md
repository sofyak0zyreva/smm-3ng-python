# Python Agent for SMM-3NG

This repository contains an implementation of a Python agent and a sample algorithm (`ConsumerAlgorithm`), intended for use within the closed SMM-3NG project.

> ⚠️ **Important**:  
> The system core, C++ agents, and other components of the project are **not available** in this repository.  
> As a result, a **full simulation cannot be run** without access to the full source code of the system.


This Repository Provides
- Implementations of agent and an example algorithm in **Python**.
- Support for interaction with the system core and other agents using **ASN.1-based communication**.


## How the Python Agent Works

The core launches each agent as a separate process.
The Python agent is started with the following arguments:

### Launch Command

```bash
python3 main.py start <instance_name> <class_name> <core_url>
```
### Agent Workflow

1. Creates a socket to receive data from other agents.
2. Connects to the core and registers itself.
3. Receives connection info (pull/push communication).
4. Interacts with other agents over **TCP**, using a custom **ASN.1-based protocol**.
5. Executes the algorithm (`algo.run()`), processes input parameters, and returns results.


## 📥 Installation

### Requirements

* Python **3.7+**
* `asn1tools` library

Install via pip

```bash
pip install asn1tools
```

## Contacts
[sofyak0zyreva](https://github.com/sofyak0zyreva) (tg @soffque)  

## License
The product is distributed under MIT license. See [`LICENSE`](LICENSE) for details.
