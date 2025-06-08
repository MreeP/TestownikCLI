# Zestawy – CLI flash-cards / quiz

## Prerequisites
* Python ≥ 3.9  
* Git (to clone the repository)

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/MreeP/TestownikCLI
cd TestownikCLI

# 2. Create and activate a virtual environment
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Preparing question sets

* Put all question sets in sub-directories under `zestawy/…`.
* Each question file must have the `.txt` extension;  
  the first line is the correct-answer mask (e.g. `1010`),  
  the second line is the question text, the following lines are the possible answers.
* The program automatically discovers all sub-directories (including nested ones).
* After the first run in a given directory, a `progress.json` file is created –  
  directories containing this file are marked with `[CONTINUE LEARNING]` in the menu.

## Running

```bash
python learn.py
```

A list of available sets will appear – navigate with the ↑ / ↓ arrow keys
and confirm with Enter.

### During the quiz
* If an image file (.png / .jpg / …) with the same base name exists, it is opened automatically:  
  * macOS – `open`  
  * Windows – default viewer (`os.startfile`)  
  * Linux – `xdg-open`
* Enter the numbers of the correct answers separated by spaces (e.g. `1 3`).
* Statistics are saved automatically after every question.

## Resetting progress

Delete the `progress.json` file inside the selected set’s directory.

## Updating dependencies

```bash
pip install -U -r requirements.txt
```
