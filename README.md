# genlayer-validator-health-check
A lightweight script for monitoring the uptime and health of GenLayer validators via their RPC endpoints.

Features
Two health checks per validator
gen_dbg_ping — fast liveness probe with latency measurement
eth_blockNumber — verifies chain progress and reports latest block
Multiple usage modes
Check default local validator (localhost:9151)
Monitor one or more remote validators
Continuous watch mode with periodic re-checks
No external dependencies
Uses only the Python standard library
Usage
# Check default validator (localhost:9151)
python check_validators.py

# Check specific validators
python check_validators.py http://validator1.example.com:9151 http://validator2.example.com:9151

# Continuous monitoring (every 30 seconds)
python check_validators.py http://validator1.example.com:9151 --watch
Output
Validator status (online/offline)
RPC responsiveness
Latency (ms)
Current block number
Summary across all nodes
Configuration

To track validators by default, edit the DEFAULT_VALIDATORS list in the script.

How it works

The script connects to each validator’s RPC endpoint (default port 9151) and performs two JSON-RPC calls:

gen_dbg_ping for basic health checks
eth_blockNumber to confirm the node is synced and progressing

Simple monitoring for GenLayer validator operators.
