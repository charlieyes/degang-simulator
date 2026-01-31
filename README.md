# Degang Simulator

AI-powered Chinese text-to-speech application featuring Guo Degang's voice simulation.

## Features

- **AI Chat**: Interactive chat with web search and page reading capabilities
- **Text-to-Speech**: Generate audio using Chinese TTS with Guo Degang's voice
- **Story Generation**: Create stories, jokes, and poems with AI assistance

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your SUPER_MIND_API_KEY
```

3. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Deployment

This application is configured for deployment to `ai-builders.space`. See `Prompts/deployment-prompt.md` for details.

## Legal Disclaimer and Terms of Use

**IMPORTANT: PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE**

This software is provided **FOR PERSONAL, EDUCATIONAL, AND RESEARCH PURPOSES ONLY**. By using this software, you agree to the following terms:

### Personal Use Only
- This project is intended **solely for personal, non-commercial use**
- **Commercial use, distribution, or monetization is strictly prohibited**
- You may not use this software to generate content for commercial purposes, including but not limited to:
  - Commercial products or services
  - Advertising or marketing materials
  - Paid content creation
  - Any form of revenue generation

### Voice Simulation and Impersonation
- This software generates audio that may simulate or resemble the voice of public figures
- **The generated audio outputs are NOT authorized by, affiliated with, or endorsed by any individuals whose voices may be simulated**
- **DO NOT use generated audio to:**
  - Impersonate individuals for fraudulent purposes
  - Create misleading or deceptive content
  - Spread false information or misinformation
  - Harass, defame, or harm individuals
  - Violate privacy rights or publicity rights
  - Commit any illegal activities

### Intellectual Property and Rights
- This project is **NOT intended to infringe upon any person's rights**, including but not limited to:
  - Right of publicity
  - Right of privacy
  - Intellectual property rights
  - Trademark rights
  - Copyrights
- Users are solely responsible for ensuring their use complies with all applicable laws and regulations
- The developers of this project assume no liability for misuse of this software

### Generative AI Disclaimer
- This software uses generative AI technology that may produce unpredictable or unintended outputs
- **No warranties or guarantees are provided** regarding the accuracy, appropriateness, or legality of generated content
- Users must exercise judgment and responsibility when using AI-generated content
- The developers are not responsible for any consequences arising from the use of generated content

### Prohibited Uses
**You may NOT use this software to:**
- Create content that violates laws or regulations
- Generate content that infringes on third-party rights
- Produce misleading, fraudulent, or deceptive content
- Harass, threaten, or harm individuals
- Create content for illegal activities
- Violate terms of service of any platform or service
- Generate content that violates privacy or data protection laws

### No Warranty
THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### User Responsibility
By using this software, you acknowledge that:
- You understand and agree to these terms
- You will use this software responsibly and legally
- You are solely responsible for any content you generate
- You will not hold the developers liable for any misuse or consequences

**If you do not agree to these terms, you must not use this software.**

---

## License

MIT License - See LICENSE file for details. Note that the MIT License does not override or supersede the legal disclaimers and terms of use stated above.
