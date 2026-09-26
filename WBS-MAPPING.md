# WBS Traceability Matrix

This document provides complete traceability between the Work Breakdown Structure (WBS) requirements for the enterprise multi-stage release pipeline and their concrete implementations in the `securemath` POC repository.

---

## Traceability Table

| WBS Code | WBS Description | POC Implementation Component | File / Configuration Reference |
| :--- | :--- | :--- | :--- |
| **Phase 2** | **Build, Obfuscation & Artifact Creation** | | |
| **2.1.1** | Provision Ubuntu build agent / container | Azure Pipelines Ubuntu-latest VM pool | `azure-pipelines.yml` (`vmImage: 'ubuntu-latest'`) |
| **2.1.2** | Install Python and build prerequisites | `UsePythonVersion@0` task and pip upgrades | `azure-pipelines.yml`, `requirements-dev.txt` |
| **2.2.1** | Create isolated virtual environment | `python -m venv .venv` isolation | `azure-pipelines.yml`, local setup guides |
| **2.2.2** | Install application dependencies | Pip installation of production/dev requirements | `requirements.txt`, `requirements-dev.txt` |
| **2.2.3** | Install PyArmor obfuscation toolchain | PyArmor package installation | `requirements-dev.txt` (`pyarmor>=9.0.0`) |
| **2.3.1** | Execute source obfuscation | Isolated PyArmor runner script | `scripts/obfuscate.py` (`pyarmor.cli gen -i`) |
| **2.3.2** | Generate obfuscated package hierarchy | Generation of protected files into dedicated path | `obfuscated/securemath/` |
| **2.3.3** | Validate obfuscation integrity & leak checks | Automated AST/token scanning for clear-text leaks | `scripts/obfuscate.py`, `tests/test_obfuscation.py` |
| **2.4.1** | Mock LicenseSpring activation abstraction | Dedicated licensing module modeling LicenseSpring | `src/securemath/license.py` |
| **2.4.2** | License verification gate | Standalone license validation script | `scripts/validate_license.py` |
| **2.4.3** | Abort pipeline on invalid/expired license | Exit code 1 handling halting build before packaging | `scripts/validate_license.py`, `azure-pipelines.yml` |
| **2.5.1** | Build Python Wheel & Source Distribution | PEP 517/518 packaging runner with `build` | `scripts/build_package.py`, `pyproject.toml` |
| **2.5.2** | Validate Wheel artifact integrity & metadata | Wheel validator checking SHA-256, naming, zip | `scripts/validate_artifact.py` |
| **2.6.1** | Upload build artifact to pipeline storage | `PublishPipelineArtifact@1` task | `azure-pipelines.yml` (`securemath-build`) |
| **Phase 3** | **Multi-OS Test Matrix** | | |
| **3.1.1** | Define Multi-OS matrix strategy | Job matrix targeting 4 distinct distributions | `azure-pipelines.yml` (`TestMatrix`) |
| **3.1.2** | Ubuntu container test environment | Ubuntu 24.04 LTS Docker container | `azure-pipelines.yml` (`ubuntu:24.04`) |
| **3.1.3** | Debian container test environment | Debian Bookworm Slim Docker container | `azure-pipelines.yml` (`debian:bookworm-slim`) |
| **3.1.4** | Alpine container test environment (musl libc) | Alpine Linux 3.20 Docker container | `azure-pipelines.yml` (`alpine:3.20`) |
| **3.1.5** | Fedora container test environment | Fedora 40 Docker container | `azure-pipelines.yml` (`fedora:40`) |
| **3.2.1** | Download build artifact in test container | `DownloadPipelineArtifact@2` task | `azure-pipelines.yml` (`securemath-build`) |
| **3.2.2** | Prepare container runtime & clean virtualenv | Package manager auto-detection and venv creation | `scripts/run_multi_os_tests.sh` |
| **3.2.3** | Install wheel in isolated clean environment | Wheel installation via pip in clean test venv | `scripts/run_multi_os_tests.sh` |
| **3.3.1** | Execute unit test suite | Pytest arithmetic test suite execution | `tests/test_calculator.py` |
| **3.3.2** | Execute licensing test suite | Pytest licensing validation test suite | `tests/test_license.py` |
| **3.3.3** | Execute obfuscation integrity test suite | Verification of obfuscated structure & import | `tests/test_obfuscation.py` |
| **3.3.4** | Execute end-to-end CLI integration test | Subprocess invocation of `securemath add` & `multiply` | `scripts/run_multi_os_tests.sh`, `tests/test_integration.py` |
| **3.4.1** | Multi-OS formatted console test output | Formatted banner reporting status per OS | `scripts/run_multi_os_tests.sh` |
| **3.4.2** | Publish test results to Azure DevOps UI | `PublishTestResults@2` JUnit reporter | `azure-pipelines.yml` |
| **Phase 4** | **Artifact Signing** | | |
| **4.1.1** | Provision secure signing environment | Ubuntu agent configured for digital signature | `azure-pipelines.yml` (`Sign` stage) |
| **4.1.2** | Retrieve build artifact from pipeline storage | `DownloadPipelineArtifact@2` task | `azure-pipelines.yml` (`securemath-build`) |
| **4.2.1** | Pre-signing SHA-256 integrity validation | SHA-256 verification against pre-computed manifest | `scripts/sign_artifact.py` |
| **4.3.1** | Digital signature generation | Cryptographic detached RSA-PSS / GPG signing | `scripts/sign_artifact.py` |
| **4.3.2** | Digital signature verification | Detached signature cryptographic verification | `scripts/verify_signature.sh`, `scripts/verify_signature.py` |
| **4.4.1** | Publish signed artifact and manifests | `PublishPipelineArtifact@1` task | `azure-pipelines.yml` (`securemath-signed`) |
| **Phase 5** | **PyPI / TestPyPI Publishing** | | |
| **5.1.1** | Provision publish environment | Ubuntu agent with Python and Twine toolchain | `azure-pipelines.yml` (`Publish` stage) |
| **5.1.2** | Retrieve signed artifact from pipeline storage | `DownloadPipelineArtifact@2` task | `azure-pipelines.yml` (`securemath-signed`) |
| **5.2.1** | Validate package archives with Twine | `twine check dist/*` pre-flight validation | `azure-pipelines.yml` |
| **5.3.1** | Secure authentication handling | Pipeline secret variable consumption (`PYPI_API_TOKEN`) | `azure-pipelines.yml` |
| **5.3.2** | Target selection (TestPyPI vs PyPI) | Pipeline parameter `publishTarget` defaulting to `testpypi` | `azure-pipelines.yml` (`publishTarget`) |
| **5.3.3** | Package upload to target repository | Secure `twine upload` execution | `azure-pipelines.yml` |
| **5.4.1** | Finalize release & notification placeholder | Build summary log with release metadata | `azure-pipelines.yml` |
| **Phase 6** | **Pipeline Governance & Branch Strategy** | | |
| **6.1.1** | Branch triggering strategy | CI triggers for `feature/*`, `develop`, `main`, `release/*` | `azure-pipelines.yml` (`trigger`, `pr`) |
| **6.1.2** | Stage conditions & execution gates | Branch-conditional execution for Signing and Publishing | `azure-pipelines.yml` (`condition`) |
| **6.1.3** | Failure scenario handling | Deterministic failures on invalid license, bad hash, bad sig | Documented in `README.md` |
