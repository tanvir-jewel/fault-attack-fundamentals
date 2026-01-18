# Fault Attack Fundamentals

Welcome to the **Fault Attack Fundamentals** repository! This is a comprehensive tutorial collection where I systematically document fault injection techniques using the ChipWhisperer platform, specifically focusing on the ChipWhisperer Husky.

## Repository Purpose

This repository serves as a step-by-step educational resource for learning fault injection attacks from the ground up. Each tutorial builds upon previous concepts, providing both theoretical understanding and practical implementation guidance.

## Tutorial Structure

The tutorials are organized progressively, starting from basic concepts and advancing to complex attack scenarios:

### Current Content
- **test_husky_parameters.py** - Script for testing and validating glitch parameters on Husky

### Planned Tutorials
- Clock glitch attack step-by-step guide
- Voltage glitch attack techniques
- Advanced parameter optimization
- Real-world target analysis
- Countermeasure evaluation

## Hardware Requirements

- ChipWhisperer Husky
- Target boards (CW313 with SAM4S recommended)
- SMA cables for voltage glitching
- USB connections

## Software Requirements

- Python 3.7+
- ChipWhisperer software suite
- Jupyter notebooks (for interactive tutorials)

## Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/tanvir-jewel/fault-attack-fundamentals.git
   cd fault-attack-fundamentals
   ```

2. Install ChipWhisperer:
   ```bash
   pip install chipwhisperer
   ```

3. Use `test_husky_parameters.py` to validate your setup

## Research Context

These tutorials are developed as part of ongoing research in hardware security and fault injection techniques. The content is based on practical experience with embedded systems security and aims to provide accessible education for researchers and practitioners.

## Contributing

Contributions are welcome! If you find errors, have suggestions for improvements, or want to add new tutorial content, please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description

## Contributors

- **Tanvir Hossain** - PhD Candidate, EECS Department, University of Kansas
  - Research Interest: Hardware Security Research
  - Email: tanvir@ku.edu
  - Website: https://www.tanvirhossain.net/

## Contact

For questions, suggestions, or collaboration inquiries:
- **Tanvir Hossain**
- Website: https://www.tanvirhossain.net/

## Educational Use

This repository is intended for educational and research purposes. All techniques demonstrated should be used responsibly and only on systems you own or have explicit permission to test.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This is an active learning repository. New tutorials and improvements are added regularly as research progresses.