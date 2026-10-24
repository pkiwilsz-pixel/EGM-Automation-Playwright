# EGM Automation & Provisioning Suite (Playwright & AI Vision)

**Watch the Demo:** [▶️ Automated EGM Test Flow](https://youtu.be/Tkheku7Vf7M)

## Overview
A Python-based Playwright automation suite engineered to eliminate repetitive manual workflows in Awager's live slot machine studio operations. This repository features an intelligent QA testing loop for live video streams and a robust administrative macro for automated backend provisioning.

## Core Modules & Features
* **`bo.py` (Backoffice Macro):** An administrative automation script designed to loop through sequential EGM ID ranges (`100001` to `100033`), dynamically filtering out offline maintenance units. It programmatically clicks through table rows and UI dialogs to rapidly provision and bring slot machines online while running completely unattended.
* **`LTH.py` (Core QA Test Loop):** A robust Playwright script connecting via Chrome DevTools Protocol (CDP) to execute automated login, lobby navigation, volume checks, 2-spin test sequences, and camera zoom checks.
* **AI-Powered UI Navigation:** Integrates the DeepSeek Vision API to analyze live video stream frames in real-time, calculating exact X/Y coordinates to interact with non-standard UI elements and bet buttons.
* **Smart State Detection & Error Handling:** Utilizes DOM polling to wait out heavy win animations and loading states, paired with programmatic exception recovery (`Escape` key fallbacks) to ensure high script resilience.
* **`Run_Automation.bat`:** A one-click desktop deployment script bypassing manual terminal paths and IDE setup.

## Tech Stack
**Python 3**, **Playwright (Sync API)**, **DeepSeek Vision API (LLM/Computer Vision)**, **Chrome CDP**, **Windows Batch Scripting**.
