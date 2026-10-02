import { useState } from 'react'

type Section = 'evaluation' | 'architecture' | 'training' | 'dataset' | 'stress'
const sections: { id: Section; name: string; number: string }[] = [
  { id: 'evaluation', name: 'Evaluation', number: '01' },
  { id: 'architecture', name: 'Architecture', number: '02' },
  { id: 'training', name: 'Training', number: '03' },
  { id: 'dataset', name: 'Dataset', number: '04' },
  { id: 'stress', name: 'Stress tests', number: '05' },
]

const perClass = [
  ['No DR', 261, '0.952', '0.985', '0.968'],
  ['Mild', 50, '0.415', '0.440', '0.427'],
  ['Moderate', 146, '0.717', '0.678', '0.697'],
  ['Severe', 25, '0.357', '0.200', '0.256'],
  ['Proliferative DR', 41, '0.417', '0.488', '0.449'],
] as const

function Chart({ src, alt, caption }: { src: string; alt: string; caption: string }) {
  return <figure className="study-chart">
    <img src={`/evidence/${src}`} alt={alt} loading="lazy" />
    <figcaption>{caption}</figcaption>
  </figure>
}

function Stat({ value, label, note, warning = false }: {
  value: string; label: string; note: string; warning?: boolean
}) {
  return <div className={`study-stat ${warning ? 'study-stat-warning' : ''}`}>
    <b>{value}</b><span>{label}</span><small>{note}</small>
  </div>
}

export default function EvidenceDashboard() {
  const [selected, setSelected] = useState<Section>('evaluation')
  return <section className="study-section" id="study" aria-labelledby="study-heading">
    <div className="study-intro">
      <div><p className="eyebrow">FROZEN NOTEBOOK EVIDENCE / APTOS 2019</p>
        <h2 id="study-heading">The research behind the result.</h2>
        <p>Explore the model, training choices and held-out evaluation. These are results from the saved Colab experiment, separate from a new upload.</p>
      </div>
      <div className="study-source"><span>FINAL COLAB EXPERIMENT</span><b>EfficientNetB0 · P2</b><small>Saved final model · 523 held-out test images</small></div>
    </div>

    <div className="study-stat-grid">
      <Stat value="3,485" label="Eligible images" note="After duplicate review" />
      <Stat value="5" label="Severity grades" note="No DR through proliferative DR" />
      <Stat value="77.1%" label="Test accuracy" note="403 / 523 correct" />
      <Stat value="0.560" label="Test Macro F1" note="Equal weight for each grade" warning />
    </div>

    <div className="study-workspace">
      <div className="study-tabs" role="tablist" aria-label="Explore coursework evidence">
        {sections.map(section => <button key={section.id} type="button" role="tab"
          id={`tab-${section.id}`} aria-controls={`panel-${section.id}`}
          aria-selected={selected === section.id} className={selected === section.id ? 'active' : ''}
          onClick={() => setSelected(section.id)}>
          <span>{section.number}</span>{section.name}<i aria-hidden="true">↗</i>
        </button>)}
        <p>Every figure is exported from the final Colab notebook. Study results describe groups of images; the analyzer below describes one upload.</p>
      </div>
      <div className="study-content" role="tabpanel" id={`panel-${selected}`} aria-labelledby={`tab-${selected}`}>
        {selected === 'evaluation' && <>
          <div className="study-heading"><span>01 / LOCKED TEST</span><h3>Performance across all five grades</h3>
            <p>The final checkpoint was selected before the held-out test was evaluated. Overall accuracy hides the weaker recall for Severe disease.</p></div>
          <div className="study-mini-grid">
            <div><b>0.572</b><span>Macro precision</span></div><div><b>0.558</b><span>Macro recall</span></div>
            <div><b>0.836</b><span>Quadratic weighted κ</span></div><div><b>20%</b><span>Severe recall · 5 / 25</span></div>
          </div>
          <div className="table-scroll"><table className="study-table"><caption>Per-class performance on the 523-image held-out test subset</caption>
            <thead><tr><th>Grade</th><th>Images</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
            <tbody>{perClass.map(([grade, n, p, r, f1]) => <tr key={grade} className={grade === 'Severe' ? 'caution-row' : ''}><th>{grade}</th><td>{n}</td><td>{p}</td><td>{r}</td><td>{f1}</td></tr>)}</tbody></table></div>
          <Chart src="test-confusion-matrix.png" alt="Five by five held-out test confusion matrix showing 257 correct No DR and five correct Severe images" caption="Colab Cell 74 · Locked test confusion matrix. Eight Severe images were predicted as Moderate and eleven as Proliferative DR." />
          <div className="study-callout">The model recognised only 5 of 25 Severe images. It is a research prototype and cannot be used for independent clinical grading.</div>
        </>}
        {selected === 'architecture' && <>
          <div className="study-heading"><span>02 / MODEL DESIGN</span><h3>Why EfficientNetB0?</h3>
            <p>A comparison with MobileNetV2 and a small tuning study selected an ImageNet-initialised EfficientNetB0 with 0.20 dropout. The saved final model was trained separately.</p></div>
          <div className="pipeline" aria-label="Final model architecture">
            <div><small>INPUT</small><strong>P2 fundus image</strong><span>224 × 224 RGB</span></div><i>→</i>
            <div><small>BACKBONE</small><strong>EfficientNetB0</strong><span>ImageNet weights</span></div><i>→</i>
            <div><small>HEAD</small><strong>Global pool + 0.20 dropout</strong><span>Five-way softmax</span></div>
          </div>
          <Chart src="architecture-comparison.png" alt="Colab bar charts comparing validation accuracy, macro F1, and Severe recall for four model candidates" caption="Colab Cell 59 · Tuning candidate: 0.826 validation accuracy and 0.670 Macro F1. Saved final model: 0.797 and 0.631 on validation." />
          <div className="study-facts"><div><b>4,055,976</b><span>Parameters in selected architecture</span></div><div><b>1 × 10⁻⁵</b><span>Fine-tuning learning rate</span></div></div>
        </>}
        {selected === 'training' && <>
          <div className="study-heading"><span>03 / EXPERIMENTAL DESIGN</span><h3>Train, monitor, then freeze</h3>
            <p>A fixed seed and split manifest kept model comparisons traceable. Augmentation and class weights were applied to training batches only.</p></div>
          <div className="phase-grid"><article><span>STAGE 01</span><h4>Classification head</h4><p>Freeze pretrained backbone · Adam 1 × 10⁻³ · up to six epochs.</p></article>
            <article><span>STAGE 02</span><h4>Fine-tune final layers</h4><p>Last 20 backbone layers eligible; BatchNorm frozen · Adam 1 × 10⁻⁵ · up to four epochs.</p></article></div>
          <Chart src="training-curves.png" alt="Training and validation loss and accuracy across six head and four fine-tuning epochs" caption="Colab Cell 69 · Training and validation curves. Best checkpoint selected by validation loss; early stopping patience was two epochs." />
          <Chart src="augmentation-balancing.png" alt="Validation results comparing augmentation and training class weights" caption="Colab Cell 55 · Combined augmentation and class weights gave 0.660 Macro F1 in the controlled comparison." />
          <p className="study-note">The two-stage learning-rate change was planned; the final training run did not use an adaptive learning-rate callback.</p>
        </>}
        {selected === 'dataset' && <>
          <div className="study-heading"><span>04 / DATA AND PREPROCESSING</span><h3>Audited before splitting</h3>
            <p>APTOS 2019 supplied 3,662 labelled photographs. Exact and reviewed near duplicates were excluded, leaving 3,485 eligible images.</p></div>
          <div className="split-list" aria-label="Frozen dataset split">
            {[['Training', 2265, '65%'], ['Validation', 523, '15%'], ['Calibration', 174, '5%'], ['Held-out test', 523, '15%']].map(([name, count, percent]) =>
              <div key={name}><span>{name}</span><div className="split-track"><i style={{ width: `${Number(count) / 3485 * 100}%` }} /></div><b>{count}</b><small>{percent}</small></div>)}
          </div>
          <Chart src="class-distribution-splits.png" alt="Stacked bars showing 1,795 No DR, 337 Mild, 921 Moderate, 168 Severe, and 264 Proliferative DR eligible images across train, validation, calibration, and test subsets" caption="Colab Cell 36 · Class distribution after duplicate review. Severe and Mild examples are scarce relative to No DR." />
          <div className="phase-grid"><article><span>P2 / INPUT</span><h4>Consistent retinal framing</h4><p>Estimate field, crop with margin, square pad and resize to 224 × 224.</p></article>
            <article><span>P2 / ENHANCE</span><h4>Local detail</h4><p>CLAHE on LAB lightness, then mild unsharp masking; RGB values remain in [0, 255] for EfficientNet.</p></article></div>
          <div className="study-callout subtle">Patient identifiers are unavailable. Image-level duplicate control cannot verify patient-independent separation.</div>
        </>}
        {selected === 'stress' && <>
          <div className="study-heading"><span>05 / CRITICAL CHECKS</span><h3>When does the model struggle?</h3>
            <p>Exploratory validation analyses use the fixed saved model and never retune the held-out test result.</p></div>
          <div className="study-mini-grid"><div><b>182 / 523</b><span>Review rule flags</span></div><div><b>81 / 106</b><span>Incorrect predictions flagged</span></div>
            <div><b>97</b><span>Predictions changed by blur</span></div><div><b>0.562</b><span>Macro F1 under blur</span></div></div>
          <Chart src="review-risk-coverage.png" alt="Risk versus coverage plot showing lower error among more confident validation predictions" caption="Colab Cell 81 · Illustrative confidence review analysis; five large grade errors remained unflagged." />
          <Chart src="shift-validation.png" alt="Validation macro F1 and prediction stability under dim, bright, blur and low contrast perturbations" caption="Colab Cell 85 · Fixed Gaussian blur lowered Macro F1 from 0.631 to 0.562; simulated changes are not external validation." />
          <p className="study-note">Grad-CAM views in the live analyzer show coarse attention associated with one predicted output. They do not identify lesions or verify a diagnosis.</p>
        </>}
      </div>
    </div>
    <div className="study-provenance">SOURCE · Final coursework notebook · Fixed split fingerprint 2c54046885a9… · Saved model fingerprint 09f075a84b4c… · Evidence charts exported from Colab outputs.</div>
  </section>
}
