# Models and licences

| Model | Use | Licence | Where it lives | How to get it |
| --- | --- | --- | --- | --- |
| Qwen2.5-7B-Instruct (`qwen2.5:7b-instruct`, 4-bit via Ollama) | Report assessment paragraph (live mode), chatbot template choice, field-assistant wording | Apache 2.0 | `OLLAMA_MODELS` (D:\VoltGuard\models\ollama) | `.\make.ps1 models` |
| Phi-3.5-mini-instruct (`phi3.5`) | Fallback model on low-memory laptops | MIT | `OLLAMA_MODELS` | `ollama pull phi3.5` (or set `LLM_MODEL`) |
| intfloat/multilingual-e5-small (ONNX) | Embeddings for RAG and similar cases (English and Bahasa Melayu) | MIT | `HF_HOME` (D:\VoltGuard\models\hf\voltguard) | `python -m voltguard fetch-models` |
| spaCy `en_core_web_sm` 3.8.0 | Presidio name, e-mail and phone detection in the notes scrubber | MIT | Python environment | installed from `backend/requirements.txt` |
| Pattern model (XGBoost) | One input of the R0 score; SHAP-style sub-reasons | Trained in-house (XGBoost: Apache 2.0) | `DATA_ROOT/models/pattern_xgb.json` | `python -m voltguard train-models` (SGCC data when loaded, else synthetic SGCC-style windows) |
| Autoencoder (scikit-learn MLP) | Anomaly score input | Trained in-house (scikit-learn: BSD-3) | `DATA_ROOT/models/autoencoder.pkl` | `python -m voltguard train-models` (normal homes of the tuning split) |
| Label model (XGBoost) | Retrained on inspection outcomes; recorded per version for R1 | Trained in-house | `DATA_ROOT/models/label-vN.json`, MLflow file store `DATA_ROOT/mlruns` | Models page -> Retrain, or `python -m voltguard retrain` |

Without the language or embedding model the app keeps working: `LLM_MODE=mock` uses deterministic
templates (with a visible "mock" badge) and RAG uses a hashing embedder. No model ever receives
personal details (SDD 8.4).
