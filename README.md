# RetinaStage Showcase

This companion website presents the saved **Diabetic Retinopathy Stage Detection** Colab experiment and demonstrates one-image inference with the same final model. The Study evidence tabs cover dataset and P2 preprocessing, architecture and transfer learning, training, held-out evaluation, and exploratory robustness checks. The charts in `web/public/evidence/` were exported from the final coursework notebook; they are fixed results, not calculations from a visitor's upload.

The included `models/selected_fine_model.keras` and `models/temperature_calibration.json` are the saved final checkpoint and calibration record. Their SHA-256 and recorded P2 preprocessing must agree before inference. The **APTOS image dataset is not included and is not needed to run the website**. Colab does not need to be rerun to show these saved results or the live analyzer.

## Run locally

Use Python 3.11 or 3.12 and a current Node.js release. From the project folder:

```bash
python3 -m venv server/.venv
server/.venv/bin/pip install -r server/requirements.txt
server/.venv/bin/uvicorn app:app --app-dir server --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd web
npm ci
npm run dev
```

Open `http://localhost:5173`. Explore the five Study evidence tabs. Then select a JPEG or PNG APTOS-style colour fundus photograph (up to 10 MB), run the analysis, inspect the five temperature-scaled grade probabilities and review flag, and view the P2 input, Grad-CAM overlay and blur check. RetinaGuide gives fixed, grounded explanations of that individual output.

If the health banner says the analyzer is unavailable, check that the API is running and both files in `models/` are present. The site never substitutes a mock model response.

## Optional gallery: ten labelled training examples

The gallery supports two original APTOS images from **each of the five grades**. The shared source ZIP does not include training photographs. To populate it, use the *final notebook's* `split_manifest.csv` and `train_images/` in Colab. If these runtime files are missing, restore the data and final manifest first; **model training and evaluation do not need to run again**. Do not select from the calibration or locked test subsets.

In Colab, run this small cell. When prompted, select `scripts/prepare_demo_gallery.py` from your Mac's website folder:

```python
from pathlib import Path
import subprocess
from google.colab import files

root = Path('/content/retinastage_data')
assert (root / 'split_manifest.csv').is_file()
assert (root / 'train_images').is_dir()
uploaded = files.upload()  # Select only prepare_demo_gallery.py
assert set(uploaded) == {'prepare_demo_gallery.py'}
Path('/content/prepare_demo_gallery.py').write_bytes(uploaded['prepare_demo_gallery.py'])
subprocess.run([
    'python', '/content/prepare_demo_gallery.py',
    '--manifest', str(root / 'split_manifest.csv'),
    '--images', str(root / 'train_images'),
    '--output', '/content/demo_examples.zip',
], check=True)
files.download('/content/demo_examples.zip')
```

On your Mac, unzip the downloaded examples into the website's public folder:

```bash
unzip -oq ~/Downloads/demo_examples.zip -d ~/Developer/RetinaStage-Showcase/web/public
```

Refresh the website to see ten cards (two per grade). Clicking a card places its original image in the analyzer; then click **Run analysis**. The exporter checks that each example belongs to the **training** split and passes the same simple upload pattern check. These training examples demonstrate the interface, **not generalisation**; cite held-out test metrics only from the notebook. The local gallery directory is ignored by Git. Kaggle lists the APTOS data as subject to its competition rules, so check those rules before hosting or sharing images publicly: https://www.kaggle.com/competitions/aptos2019-blindness-detection/data

## Upload screening and limits

The browser limits the chooser to JPEG/PNG. On selection, the API checks the decoded file, dimensions, maximum pixel count, and simple colour/lighting cues of a circular fundus field; only an accepted image is shown in the input. The check runs again **before** model inference. Its lighting check compares the retinal field with the image's own corners, which allows some dark photographs. It rejects many ordinary photographs, screenshots, diagrams, and invalid files. This heuristic cannot prove that an image is a real retina: a crafted unrelated image may pass, and a genuine atypical, extremely dark or tightly cropped fundus photo may be rejected. A passed image is not a quality certificate.

This is an educational prototype, not a clinical diagnostic service. On the locked 523-image test set, the saved model achieved 77.1% accuracy and 0.560 macro F1, but Severe recall was only 5/25 (20%). The dataset lacks patient identifiers, so patient-independent separation could not be verified. The review rule, heatmap, and blur check are exploratory aids, not clinical safeguards or external validation. Do not upload identifiable patient images for a public demonstration. The API does not save uploaded image files; it retains compact result summaries in memory for up to 30 minutes so RetinaGuide can answer questions.

## Checks

```bash
python3 -m unittest discover -s server/tests -v
cd web && npm run build
```

The pure Python tests check guide responses and upload-screen examples. The full inference API needs the Python packages in `server/requirements.txt`, including TensorFlow. The notebook is the authoritative source for training, splits, calibration and evaluation; the site shows a curated read-only selection of its outputs.

## Record the prototype

Start the API and frontend, then record the site in operation: show the Evaluation tab and its confusion matrix, Architecture, Training and Dataset tabs, select a permissible demonstration fundus image, run inference, inspect the probabilities and attention/blur panels, and ask RetinaGuide a question. Briefly show rejection of an ordinary non-retinal picture if desired. Explain that the Study charts are saved Colab results and the one-image analysis is a new live prediction. Add the hosted video URL to the coursework PDF report.

`models/` is excluded from Git by `.gitignore`; the supplied ZIP includes the checkpoint for local demonstration. Do not commit the model, Kaggle token, private retinal images or patient data to a public repository.
