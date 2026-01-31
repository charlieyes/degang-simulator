# Models Directory

Place your trained model weights here:

- `gpt_weights.ckpt` - Your GPT model (text-to-semantic)
- `sovits_weights.pth` - Your SoVITS model (semantic-to-audio)

## Also needed:

- `prompt_semantic.pt` - Pre-extracted semantic token tensor (place in root directory)
- `reference.wav` - Reference audio file for refer_spec extraction (place in root directory)

## How to extract prompt_semantic:

If you need to extract prompt_semantic from a reference audio, you can use the original GPT-SoVITS codebase or extract it using:

```python
import torch
import librosa
from GPT_SoVITS.feature_extractor.cnhubert import CNHubert
from GPT_SoVITS.module.models import SynthesizerTrn

# Load models (temporary, just for extraction)
cnhubert = CNHubert("path/to/chinese-hubert-base")
vits_model = SynthesizerTrn(...)  # Load your SoVITS model

# Extract from audio
wav16k, sr = librosa.load("reference.wav", sr=16000)
wav16k = torch.from_numpy(wav16k)
hubert_feature = cnhubert.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)
codes = vits_model.extract_latent(hubert_feature)
prompt_semantic = codes[0, 0]

# Save
torch.save(prompt_semantic, "prompt_semantic.pt")
```
