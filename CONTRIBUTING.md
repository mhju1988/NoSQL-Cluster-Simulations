# Contributing to NoSQL Cluster Simulations

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Relevant logs or error messages

### Suggesting Enhancements

We welcome suggestions for:
- New chaos scenarios
- Additional monitoring metrics
- Performance improvements
- Documentation improvements

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/NoSQL-Cluster-Simulations.git
   cd NoSQL-Cluster-Simulations
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Start the environment
   ./start.sh

   # Test your changes
   # ...

   # Run existing tests
   docker exec test-orchestrator python test_framework.py
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Guidelines

### Adding New Chaos Scenarios

1. Add the scenario to `chaos/chaos-scenarios.sh`:
   ```bash
   scenario_my_new_scenario() {
       local duration=${1:-30}
       log_warning "SCENARIO: My New Scenario"

       # Inject chaos here

       wait_for_recovery "$duration"

       log_info "Scenario ended"
   }
   ```

2. Add it to the menu in the same file

3. Create a corresponding test in `test-orchestrator/test_framework.py`:
   ```python
   ChaosScenario(
       name="My New Scenario",
       description="What this scenario does",
       duration=30,
       inject_fn=lambda: self._my_chaos_injection(),
       recover_fn=lambda: self._my_recovery()
   )
   ```

### Adding Monitoring Metrics

1. Update Prometheus configuration in `monitoring/prometheus/prometheus.yml`

2. Add new panels to Grafana dashboard in `monitoring/grafana/dashboards/mongodb-cluster.json`

3. Document the new metrics in README.md

### Code Style

**Python:**
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Maximum line length: 100 characters

**Bash:**
- Use `set -e` for error handling
- Quote variables: `"$variable"`
- Use functions for reusable code
- Add comments for complex logic

**Docker/YAML:**
- Use 2-space indentation
- Keep resource limits reasonable for testing
- Document environment variables

## Testing Checklist

Before submitting a pull request:

- [ ] Code follows project style guidelines
- [ ] All scripts are executable (`chmod +x`)
- [ ] Changes are documented in README.md
- [ ] New chaos scenarios have corresponding tests
- [ ] Docker Compose configuration is valid
- [ ] Environment starts successfully with `./start.sh`
- [ ] No sensitive data (passwords, keys) in commits
- [ ] Results directory is not committed (except .gitkeep)

## Project Structure

When adding files, follow this structure:

```
NoSQL-Cluster-Simulations/
├── chaos/                  # Chaos engineering scenarios
├── monitoring/             # Monitoring configurations
│   ├── prometheus/        # Prometheus config
│   └── grafana/          # Grafana dashboards
├── scripts/               # Initialization scripts
├── test-orchestrator/     # Load testing and automation
└── results/               # Test results (gitignored)
```

## Communication

- **Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For questions and general discussion

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please open an issue with the "question" label.

---

Thank you for contributing to NoSQL Cluster Simulations! 🎉
