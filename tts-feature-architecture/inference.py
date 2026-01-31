"""
Minimal Chinese TTS Inference Script
Ready to use with pre-extracted prompt_semantic features
"""

import os
import sys
import torch
import soundfile as sf
import numpy as np

# Add GPT_SoVITS to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'GPT_SoVITS'))

from GPT_SoVITS.TTS_infer_pack.TTS import TTS


class ChineseTTS:
    """Minimal Chinese TTS wrapper for deployment"""
    
    def __init__(self, gpt_path, sovits_path, bert_path=None, device="cuda", is_half=True, version="v2"):
        """
        Initialize Chinese TTS model
        
        Args:
            gpt_path: Path to GPT model weights (.ckpt)
            sovits_path: Path to SoVITS model weights (.pth)
            bert_path: Path to BERT model directory (default: auto-detect)
            device: "cuda" or "cpu"
            is_half: Use half precision (faster, less memory)
            version: Model version ("v2", "v2Pro", "v2ProPlus", "v3", "v4")
        """
        if bert_path is None:
            # Use TTS_BASE_PATH from env if available, otherwise use current_dir
            tts_base_path = os.environ.get("TTS_BASE_PATH")
            if tts_base_path:
                bert_path = os.path.join(tts_base_path, "tts-feature-architecture", "GPT_SoVITS", "pretrained_models", "chinese-roberta-wwm-ext-large")
                bert_path = os.path.normpath(bert_path)
            else:
                bert_path = os.path.join(current_dir, "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large")
        
        # CNHubert path - optional, only needed if extracting features from new audio
        # Since we use pre-extracted reference_semantic.pt, CNHubert is not required
        cnhuhbert_path = None
        
        config = {
            "version": version,
            "custom": {
                "t2s_weights_path": gpt_path,
                "vits_weights_path": sovits_path,
                "bert_base_path": bert_path,
                "cnhuhbert_base_path": cnhuhbert_path,  # Needed for extracting features from audio
                "device": device,
                "is_half": is_half,
            }
        }
        print("Initializing TTS model...")
        self.tts = TTS(config)
        print("[OK] TTS model initialized")
        
    def set_reference(self, prompt_semantic=None, refer_spec=None, ref_audio_path=None):
        """
        Set reference audio features
        
        Args:
            prompt_semantic: Pre-extracted semantic token tensor [1024] or path to .pt file (optional)
            refer_spec: Reference spectrogram tuple (spec, audio_tensor) (optional)
            ref_audio_path: Path to reference audio (optional, will extract both if prompt_semantic is None)
        """
        # If prompt_semantic is provided, use it
        if prompt_semantic is not None:
            # Load prompt_semantic if it's a path
            if isinstance(prompt_semantic, (str, os.PathLike)):
                prompt_semantic = torch.load(prompt_semantic, map_location=self.tts.configs.device)
            
            # Ensure it's on the right device
            if isinstance(prompt_semantic, torch.Tensor):
                prompt_semantic = prompt_semantic.to(self.tts.configs.device)
            
            self.tts.prompt_cache["prompt_semantic"] = prompt_semantic
            print(f"[OK] Set prompt_semantic: shape {prompt_semantic.shape}")
        
        # Handle refer_spec
        if refer_spec is not None:
            self.tts.prompt_cache["refer_spec"] = [refer_spec]
            print("[OK] Set refer_spec from provided tensor")
        elif ref_audio_path is not None:
            if not os.path.exists(ref_audio_path):
                raise FileNotFoundError(f"Reference audio not found: {ref_audio_path}")
            
            # If prompt_semantic not provided, extract it from audio
            if prompt_semantic is None:
                print("Extracting prompt_semantic from reference audio...")
                self.tts.set_ref_audio(ref_audio_path)  # This extracts both prompt_semantic and refer_spec
            else:
                # Only extract refer_spec
                self.tts._set_ref_spec(ref_audio_path)
                print(f"[OK] Extracted refer_spec from {ref_audio_path}")
        else:
            if prompt_semantic is None:
                raise ValueError("Either prompt_semantic or ref_audio_path must be provided")
    
    def synthesize(self, text, prompt_text=None, output_path=None, top_k=20, top_p=0.6, 
                   temperature=0.6, speed=1.0, **kwargs):
        """
        Synthesize Chinese text to audio
        
        Args:
            text: Chinese text to synthesize
            prompt_text: Reference text (optional, defaults to text if None)
            output_path: Path to save audio (optional)
            top_k: Top-k sampling parameter
            top_p: Top-p sampling parameter
            temperature: Temperature for sampling
            speed: Speed factor (1.0 = normal)
            **kwargs: Additional TTS parameters
        
        Returns:
            audio: numpy array (float32, range [-1, 1])
            sample_rate: int
        """
        # For reference audio-based synthesis, use empty prompt_text to avoid early stopping
        # The prompt_semantic from reference audio provides voice/style, but shouldn't constrain text matching
        if prompt_text is None:
            prompt_text = ""  # Empty string - will use prompt=None internally, allowing full generation
            print("Note: Using empty prompt_text to allow full audio generation from reference voice")
        
        inputs = {
            "text": text,
            "text_lang": "zh",
            "ref_audio_path": None,  # Already set via set_reference()
            "prompt_text": prompt_text,
            "prompt_lang": "zh",
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": "cut0",  # Simple segmentation
            "batch_size": 1,
            "speed_factor": speed,
            "return_fragment": False,
            **kwargs
        }
        
        audio_chunks = []
        sample_rate = None
        
        for sr, audio in self.tts.run(inputs):
            sample_rate = sr
            audio_chunks.append(audio)
        
        if len(audio_chunks) == 0:
            raise RuntimeError("No audio generated")
        
        # Concatenate all chunks
        final_audio = np.concatenate(audio_chunks)
        
        # Convert to float32 and normalize to [-1, 1] range
        # TTS returns int16 audio (range [-32768, 32768])
        if final_audio.dtype == np.int16:
            final_audio = final_audio.astype(np.float32) / 32768.0
        elif final_audio.dtype == np.int32:
            final_audio = final_audio.astype(np.float32) / 2147483648.0
        else:
            final_audio = final_audio.astype(np.float32)
        
        # Check if audio is already normalized or needs normalization
        max_val = np.max(np.abs(final_audio))
        
        # If max_val > 1, it's likely already in int16 range but not normalized
        if max_val > 1.0:
            final_audio = final_audio / max_val * 0.95  # Normalize to 95% to avoid clipping
        # If max_val is between 0.01 and 1.0, it might be partially normalized
        # If max_val < 0.01, the audio is very quiet - normalize it
        elif max_val > 0.0:
            # Normalize quiet audio to make it audible
            final_audio = final_audio / max_val * 0.95
        
        if output_path:
            sf.write(output_path, final_audio, sample_rate)
            print(f"[OK] Saved audio to {output_path}")
        
        return final_audio, sample_rate


# Example usage
if __name__ == "__main__":
    # Configuration - Model paths (already set up)
    GPT_MODEL_PATH = "models/gpt_weights.ckpt"
    SOVITS_MODEL_PATH = "models/sovits_weights.pth"
    PROMPT_SEMANTIC_PATH = "prompt_semantic.pt"  # Your pre-extracted feature
    REF_AUDIO_PATH = "reference.wav"  # Reference audio for refer_spec
    
    # Check if files exist
    if not os.path.exists(GPT_MODEL_PATH):
        print(f"Error: GPT model not found at {GPT_MODEL_PATH}")
        print("Please place your GPT model weights (.ckpt) in the models/ directory")
        sys.exit(1)
    
    if not os.path.exists(SOVITS_MODEL_PATH):
        print(f"Error: SoVITS model not found at {SOVITS_MODEL_PATH}")
        print("Please place your SoVITS model weights (.pth) in the models/ directory")
        sys.exit(1)
    
    # Initialize TTS
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    tts = ChineseTTS(
        gpt_path=GPT_MODEL_PATH,
        sovits_path=SOVITS_MODEL_PATH,
        device=device,
        is_half=(device == "cuda"),
        version="v2ProPlus"  # Model version (matches your GuoDeGang models - v2ProPlus)
    )
    
    # Set reference
    if os.path.exists(PROMPT_SEMANTIC_PATH):
        tts.set_reference(
            prompt_semantic=PROMPT_SEMANTIC_PATH,
            ref_audio_path=REF_AUDIO_PATH
        )
    else:
        print(f"Warning: {PROMPT_SEMANTIC_PATH} not found.")
        print("Using ref_audio_path to extract both prompt_semantic and refer_spec")
        tts.tts.set_ref_audio(REF_AUDIO_PATH)
    
    # Synthesize Chinese text
    test_text = "你好，这是一个测试。"
    output_file = "output.wav"
    
    audio, sr = tts.synthesize(
        text=test_text,
        prompt_text="",  # Can be empty if you don't need prompt text
        output_path=output_file,
        top_k=20,
        top_p=0.6,
        temperature=0.6,
        speed=1.0
    )
    
    print(f"\n[OK] Generated {len(audio)} samples at {sr} Hz")
    print(f"[OK] Audio saved to {output_file}")
