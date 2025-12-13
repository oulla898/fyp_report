import { GoogleGenAI } from '@google/genai'
import { promises as fs } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const MODEL_NAME = 'gemini-3-pro-image-preview'
const OUTPUT_DIR = path.resolve(__dirname, '..', 'figures')
const PROJECT_ROOT = path.resolve(__dirname, '..')

const VISUAL_ABSTRACT_PROMPT = `Create a single, publication-ready graphical abstract for a research thesis on autonomous mobile robots (AMRs) in hospitals.

The tone must be strictly scientific and neutral. Do not use marketing language, emotional wording, or vague adjectives. Use only clear, factual phrases that could appear in a peer-reviewed journal.

Overall style:
- Clean, minimalist academic design on a white or very light grey background.
- Flat, vector-style illustrations; no photos, no 3D effects.
- Limited professional palette (e.g., dark blue, grey, muted teal) with high contrast for readability.
- No decorative flourishes; every element must communicate information.

Canvas and layout (horizontal 16:9 figure):

1) Header strip (top 10–15% of width):
- Left: concise title in one line: "Autonomous Mobile Robot for Hospital Logistics".
- Right: short subtitle in one line: "Evidence-based benefits in clinical environments".
- Use a simple sans-serif font suitable for scientific figures.

2) Left panel (about 35–40% of width): system overview
- Draw a simplified hospital corridor or floor outline (few rooms and a nurse station) in thin grey lines.
- Place one AMR icon in the corridor: a small wheeled base with a vertical body and a top sensor.
  - Indicate LiDAR sensor as a small cylinder on top.
  - Indicate a front tablet/screen panel on the body.
- Show a simple path or arrows along the corridor to indicate autonomous navigation.
- Under or beside the robot, add three short technical labels only:
  - "ROS 2 navigation"
  - "LiDAR-based SLAM"
  - "Task scheduling for deliveries"

3) Centre panel (about 25–30% of width): information flow
- Draw a compact block diagram with 3 rectangular boxes stacked vertically and connected by arrows:
  - Box 1 label: "Task requests" (e.g., medications, meals, linens, lab samples).
  - Box 2 label: "AMR control stack" with a smaller sub-label inside: "perception, planning, safety".
  - Box 3 label: "Executed hospital missions".
- Arrows must be clear and straight; no decorative curves.
- Optionally add one small side arrow labelled "Status to staff dashboard" to show feedback to staff.

4) Right panel (about 35–40% of width): evidence-based benefits grid
- Organise the benefits in a 2×3 grid of small panels with an icon and a very short text label in each.
- Each cell must correspond directly to findings from the literature review section "Benefits of Autonomous Mobile Robots in Healthcare Settings" and use precise, non-promotional wording.

Use exactly the following six benefit cells and text (no extra benefits, no emojis):
1. Top-left cell: icon of shield over a bed.
  - Text line 1: "Reduced human contact"
  - Text line 2: "supports infection control"



2. Top-right cell: icon of a person with a guiding arrow or map.
  - Text line 1: "Wayfinding and guidance"
  - Text line 2: "visitor support and navigation"

3. Bottom-left cell: icon of stacked boxes on a cart.
  - Text line 1: "Material transport automation"
  - Text line 2: "up to ~30% logistics time saving"

4. Bottom-centre cell: icon of a screen with two faces connected, or a robot with a video call bubble.
  - Text line 1: "Telepresence and remote access"
  - Text line 2: "consultations without travel"

5. Bottom-right cell: icon of a biohazard container on wheels.
  - Text line 1: "Waste handling and exposure reduction"
  - Text line 2: "limits staff contact with hazardous loads"

Text rules:
- Keep all wording short and technical, with no selling language.
- Do not add exclamation marks, slogans, or subjective adjectives like "amazing" or "revolutionary".
- Use only the exact benefit texts provided above plus the title, subtitle, and three technical labels.

Output:
- A single 16:9 PNG figure suitable to paste into a thesis as a graphical abstract.
- The figure must clearly and quietly summarise: (a) what the AMR does in the hospital, and (b) the main evidence-based benefits reported in recent deployments, as specified above.
`

const LEVEL0_PROMPT = `Create a clean, Level 0 functional block diagram for the smart healthcare robot described below.

Tone and style:
- Strictly technical and academic; no marketing language or emotional wording.
- White or very light grey background, flat vector style, thin dark-grey or dark-blue lines.
- No decorative elements; every label or arrow must convey information.

System context (from the thesis): at Level 0 the robot is treated as a single black-box system with external interfaces.

Layout (horizontal 16:9 diagram):

1) Central system block (middle of the canvas)
- A large rectangular block labelled on two lines:
  Line 1 (title): "Smart Healthcare Robot"
  Line 2 (subtitle): "System Level 0 – Black Box View" (smaller text)

2) Left side: Inputs group
- Draw one grouped box on the left side titled "Inputs".
- Inside this box, list the following items as short bullet-like labels (each on its own line, no long sentences):
  - "Voice commands from patients and staff"
  - "Touch input via tablet interface"
  - "Remote task requests from web dashboard"
  - "Environmental sensor data (LiDAR, camera)"
  - "Power from charging station"
- Draw multiple arrows from the Inputs group into the central "Smart Healthcare Robot" block to indicate information and energy flow.

3) Right side: Outputs group
- Draw one grouped box on the right side titled "Outputs".
- Inside this box, list the following items as short labels:
  - "Locomotion in hospital environment"
  - "Voice responses (text-to-speech)"
  - "Visual feedback on tablet display"
  - "Telemetry to monitoring systems"
  - "Physical item delivery"
- Draw arrows from the central block out to the Outputs group.

4) Bottom: Primary functions
- Beneath the central block, add a horizontal box or area titled "Primary functions".
- Inside, list the main functions as concise phrases (each as a bullet or separate line):
  - "Autonomous navigation and obstacle avoidance"
  - "Natural language interaction with users"
  - "Task execution: delivery, information, telepresence"
  - "Status monitoring and reporting"
  - "Autonomous recharging"
- Connect this "Primary functions" area to the central block with simple arrows or clear visual association.

Diagram rules:
- Use only straight arrows; avoid curved decorative connectors.
- Keep text short, with no extra commentary beyond the items provided.
- Fonts should be simple and readable in a printed thesis figure.

Output:
- One 16:9 PNG diagram that clearly shows the Level 0 black-box functional view with Inputs, Smart Healthcare Robot block, Outputs, and Primary functions as specified above.
`

const LEVEL1_PROMPT = `Create a Level 1 functional decomposition diagram for the same smart healthcare robot. This figure should expand the central block into its main subsystems and show their key responsibilities and interfaces.

Tone and style:
- Same academic, neutral style as the Level 0 diagram: white background, flat vector shapes, thin dark-grey or dark-blue lines, no decoration.
- All wording must be short, factual, and easy to read in a thesis.

System description (from the thesis): the robot is decomposed into seven subsystems:
- Mobility
- Navigation
- Perception
- Intelligence
- Task Management
- Interface and Communication
- Power Management

Layout suggestion (horizontal 16:9 diagram):

1) Title area (top)
- At the top, place a clear title: "System Level 1 – Subsystem Decomposition".

2) Central coordination subsystem
- Place the "Task Management" subsystem as a medium-sized box in the centre of the diagram.
- Inside the box, add a one-line responsibility summary: "queue and prioritise tasks; coordinate deliveries and missions".

3) Surrounding subsystems
- Arrange the remaining subsystems around Task Management as separate labelled boxes:

  a) "Navigation" box, slightly above and to the left of Task Management.
     - Inside text: "map building, localisation, path planning, obstacle avoidance".

  b) "Mobility" box, below Navigation.
     - Inside text: "execute velocity commands; provide odometry; emergency stop".

  c) "Perception" box, to the left side.
     - Inside text: "camera, microphones, proximity sensors; environment sensing".

  d) "Intelligence" box, above Task Management.
     - Inside text: "Gemini-based natural language understanding and response".

  e) "Interface and Communication" box, to the right side.
     - Inside text: "tablet UI, web dashboard, network communication".

  f) "Power Management" box, below and slightly to the right.
     - Inside text: "battery, BMS, converters, docking and charging".

4) Key interfaces (arrows and labels)
- Show clear arrows for the main data and command flows, using short labels where helpful:

  - From "Task Management" to "Navigation": arrow labelled "navigation goals".
  - From "Navigation" to "Mobility": arrow labelled "velocity commands".
  - From "Mobility" back to "Navigation": arrow labelled "odometry".
  - From "Perception" to "Navigation": arrow labelled "sensor data (LiDAR, proximity)".
  - From "Perception" to "Intelligence": arrow labelled "audio and video".
  - From "Interface and Communication" to "Task Management": arrow labelled "task requests and status".
  - From "Intelligence" to "Task Management": arrow labelled "high-level task requests".
  - From "Power Management" to "Task Management" and "Interface": arrows labelled "battery status".
  - From "Task Management" to "Power Management": arrow labelled "dock / charge command".

Diagram rules:
- Do not add extra subsystems beyond the seven listed.
- Keep all arrows straight and avoid overlapping labels wherever possible.
- Ensure subsystem names match exactly: "Mobility", "Navigation", "Perception", "Intelligence", "Task Management", "Interface and Communication", "Power Management".

Output:
- One 16:9 PNG figure suitable as the "System Level 1 – Subsystem Decomposition" diagram in the thesis.
`

async function ensureOutputDir(): Promise<void> {
  await fs.mkdir(OUTPUT_DIR, { recursive: true })
}

async function generateImage(prompt: string, baseFilename: string, label: string): Promise<void> {
  const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY })

  console.log(`🎨 Generating ${label}...`)

  const response = await ai.models.generateContentStream({
    model: MODEL_NAME,
    config: {
      responseModalities: ['IMAGE', 'TEXT'],
      imageConfig: {
        aspectRatio: '16:9',
        imageSize: '2K'
      }
    },
    contents: [
      {
        role: 'user',
        parts: [{ text: prompt }]
      }
    ]
  })

  let imageGenerated = false
  for await (const chunk of response) {
    const part = chunk.candidates?.[0]?.content?.parts?.[0]
    
    if (part?.inlineData) {
      const outputPath = path.join(OUTPUT_DIR, `${baseFilename}-${Date.now()}.png`)
      const imageData = part.inlineData.data ?? ''
      await fs.writeFile(outputPath, Buffer.from(imageData, 'base64'))
      console.log(`✅ ${label} saved: ${outputPath}`)
      imageGenerated = true
    } else if (chunk.text) {
      console.log('ℹ️  Model note:', chunk.text)
    }
  }

  if (!imageGenerated) {
    console.warn(`⚠️  No image was generated for ${label}. Check the model response.`)
  }
}

async function main() {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error('GEMINI_API_KEY is not set. Please set it in your environment.')
  }

  await ensureOutputDir()

  // System Level 0 functional view only
  await generateImage(LEVEL0_PROMPT, 'level0-functional-view', 'Level 0 functional diagram')

  // System Level 1 subsystem decomposition only
  await generateImage(LEVEL1_PROMPT, 'level1-subsystem-decomposition', 'Level 1 subsystem diagram')

  console.log('\n✨ Level 0 and Level 1 image generation complete!')
  console.log('📁 Check the figures/ directory for the new outputs')
}

main().catch(err => {
  console.error('❌ Generation failed:', err)
  process.exit(1)
})
