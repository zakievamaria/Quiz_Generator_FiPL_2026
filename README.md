# Web Trainer for French Language
## Goal of this instruction
To teach the user how to use the web‑based French language trainer with interactive flashcards. 
The documentation covers local server launch, navigation, and the five exercise types.
## Target audience
The instruction is designed for students, teachers, and anyone learning French. The target audience is expected to have basic computer skills (installing programs, using command line, browsing the web).
## Context
The application is built on a local Flask server and runs entirely on your computer.
All exercises are generated on the client side (in the browser) and do not require an internet connection after installation.
Future versions will allow generating exercises from uploaded text files.
## Launching the Application
### Step 1. Install Python
Make sure `Python 3.8` or higher is installed on your computer.
If not, download it from the official website: [python.org](https://www.python.org/downloads/).
During installation, check the option Add Python to PATH (Windows).
Verify the installation by opening a terminal (command prompt) and typing:
```commandline
python --version
```
You should see the version number (e.g., `Python 3.10.5`).

### Step 2. Download the project
Copy the project folder to a convenient location on your computer. If you use GitHub, clone the repository or download a ZIP archive.

### Step 3. Start the server
1. Navigate to the project folder in the terminal:
```commandline
cd C:\path\to\exercise_generator    # for Windows
cd /path/to/exercise_generator      # for macOS/Linux
```
2. Install dependencies:
```commandline
pip install -r requirements.txt
```
3. Run the application:
```commandline
python src/web/app.py
```
3. The terminal will show:
```text
* Running on http://127.0.0.1:5000
```
This means the server is running.
### Step 4. Open the application in a browser
Open any web browser and enter the following address:
```text
http://127.0.0.1:5000
```
You will see the main page of the trainer.

* Important! Do not close the terminal while using the application. To stop the server, press `Ctrl + C` in the terminal.
## Site Structure
After launching, the header contains two navigation items:

* **Home** – the main page with exercises.
* **About us** – a page with developer contact information, a link to the GitHub repository, and links to both user and technical documentation.

The main page is divided into three columns:

* **Left column** – exercise type selection:

  1. True / False
  2. Matching
  3. Word Order
  4. Fill blanks
  5. Multiple Choice

* **Central column** – the current task and the answer input area.

* **Right column** – file upload and preview area.
## Exercise Types
1. **True / False**

You are presented with a statement (e.g., *“Le chat est un mammifère”*). You must decide whether it is True or False.
After clicking `«Посмотреть ответ»` (Show answer), your choice is highlighted green (correct) or red (incorrect), and a message appears below.

2. **Matching**

Two lists are shown:

* **Words** (e.g., *“chat”, “chien”, “soleil”*)

* **Definitions** (e.g., *“animal domestique”, “animal de compagnie”, “astre”*)
For each word, select the correct definition from a drop‑down menu.
Upon checking, correctly matched pairs turn green, incorrect ones turn red.

3. **Word Order**

A sentence with scrambled words is displayed, for example: *“aime / je / les chats”*.
Use the drop‑down menus in the correct order to reconstruct the sentence.
After checking, the order is considered correct only if all words are in the right positions.

4. **Fill blanks**

A sentence with numbered gaps appears, e.g., *“1. Je ___ les chats. 2. Il ___ à la maison.”*
Type the missing words into the text fields.
During verification, each field is highlighted green (correct) or red (incorrect). An overall result is shown.

5. **Multiple Choice**

You are given a question, often about synonyms or antonyms, with several options. For example:

*Find the synonym of “heureux”:
a) triste
b) content
c) fatigué*

Select answer. After checking, the correct option is highlighted green; the user’s choice is green if correct, otherwise red.
_____
* **Unlimited attempts** – you can check your answers as many times as you like. Each time you press «Посмотреть ответ», the form is re‑evaluated and feedback is updated.
______
## Working with Text Files
### Uploading a text file
In the right column, click `«Выберите файл»` (Choose file).

Select a text file in `.txt` format.

The file content appears in the preview area.

The uploaded text can be used to automatically generate exercises.
## Closing the Application
To stop the application:

1. Return to the terminal where the server is running.

2. Press `Ctrl + C`.

3. Close the browser tab.

## Additional Information
* All exercises work **offline** (after installation).

* If you modify project files (e.g., add new texts), you must restart the server (stop with `Ctrl+C` and run `python app.py` again).
___
For any questions regarding installation or usage, **visit the `About us` page for developer contacts and a link to the repository with source code.**
_____