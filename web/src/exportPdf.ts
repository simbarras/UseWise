import jsPDF from 'jspdf';
import { type PPSummary, getRiskLevel, getRiskScore } from './api';

const PRIMARY   = [30, 41, 59]   as const;  // slate-800
const SECONDARY = [56, 189, 248] as const;  // cyan
const GREEN     = [16, 185, 129] as const;
const RED       = [239, 68, 68]  as const;
const GRAY      = [100, 116, 139]as const;
const LIGHTGRAY = [241, 245, 249]as const;

// ─────────────────────────────────────────────────────────────────────────────
// LOGO BASE64
// Pour générer le base64 de ton logo :
//   cd ~/EPFL/Law_Computation/UseWise/public
//   base64 -w 0 logo.png
// Puis colle le résultat ci-dessous avec le préfixe data:image/png;base64,
// Exemple : 'data:image/png;base64,iVBORw0KGgoAAAANS...'
// ─────────────────────────────────────────────────────────────────────────────
const LOGO_BASE64 = ''; // ← COLLE TA STRING BASE64 ICI
const LOGO_WIDTH  = 14; // largeur du logo dans le PDF (mm) — ajuste si besoin
const LOGO_HEIGHT = 14; // hauteur du logo dans le PDF (mm) — ajuste si besoin

export function exportToPdf(
  data: PPSummary,
  messages: { from: 'user' | 'ai'; text: string }[]
) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const W   = 210;
  const PAD = 18;
  let   y   = 0;

  // helpers
  const setColor = (rgb: readonly [number, number, number]) => doc.setTextColor(...rgb);
  const setFill  = (rgb: readonly [number, number, number]) => doc.setFillColor(...rgb);
  const setDraw  = (rgb: readonly [number, number, number]) => doc.setDrawColor(...rgb);
  const text     = (str: string, x: number, yy: number, opts?: any) => doc.text(str, x, yy, opts);
  const newPage  = () => { doc.addPage(); y = PAD; };
  const checkY   = (needed = 12) => { if (y + needed > 275) newPage(); };

  // HEADER
  setFill(PRIMARY);
  doc.rect(0, 0, W, 22, 'F');

  // Logo à gauche (si fourni)
  if (LOGO_BASE64) {
    doc.addImage(LOGO_BASE64, 'PNG', PAD, 4, LOGO_WIDTH, LOGO_HEIGHT);
  }

  // Titre décalé à droite du logo
  const titleX = LOGO_BASE64 ? PAD + LOGO_WIDTH + 3 : PAD;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  setColor([255, 255, 255]);
  text('UseWise', titleX, 14);

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  setColor([148, 163, 184]);
  text('Privacy Policy Analysis Report', titleX, 19);

  // Date en haut à droite
  const date = new Date().toLocaleDateString('en-GB');
  setColor([148, 163, 184]);
  text(date, W - PAD, 19, { align: 'right' });

  y = 32;

  // RISK LEVEL
  const riskLabel = getRiskLevel(data.risk_level);
  const riskScore = getRiskScore(data.risk_level);
  const riskColor = riskLabel === 'Low' ? GREEN : riskLabel === 'Medium' ? [245, 158, 11] as const : RED;

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  setColor(PRIMARY);
  text('Risk Level', PAD, y);

  setFill(riskColor);
  doc.roundedRect(PAD + 30, y - 5, 22, 7, 2, 2, 'F');
  doc.setFontSize(8);
  setColor([255, 255, 255]);
  text(riskLabel.toUpperCase(), PAD + 31, y - 0.5);

  doc.setFontSize(9);
  setColor(GRAY);
  doc.setFont('helvetica', 'normal');
  text(`(${data.risk_level}/5 \u2014 ${riskScore}%)`, PAD + 56, y);

  y += 5;

  setFill(LIGHTGRAY);
  doc.roundedRect(PAD, y, W - PAD * 2, 3, 1, 1, 'F');
  setFill(riskColor);
  doc.roundedRect(PAD, y, ((W - PAD * 2) * riskScore) / 100, 3, 1, 1, 'F');

  y += 12;

  // FLASH SUMMARY
  checkY(10);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12);
  setColor(PRIMARY);
  text('Flash Summary', PAD, y);
  y += 2;

  setDraw(SECONDARY);
  doc.setLineWidth(0.5);
  doc.line(PAD, y, PAD + 40, y);
  y += 6;

  data.summaries.forEach((s) => {
    checkY(8);
    const col = s.present ? GREEN : RED;
    const sym = s.present ? '\u2713' : '\u2717';

    setFill(col);
    doc.circle(PAD + 2.5, y - 1.5, 2.5, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    setColor([255, 255, 255]);
    text(sym, PAD + 1.2, y - 0.3);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    setColor(PRIMARY);
    const lines = doc.splitTextToSize(s.flash, W - PAD * 2 - 10) as string[];
    lines.forEach((line, i) => text(line, PAD + 8, y + i * 4.5));
    y += lines.length * 4.5 + 3;
  });

  y += 4;

  // AI SUMMARY
  if (data.summaries.length > 0) {
    checkY(10);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    setColor(PRIMARY);
    text('AI Summary', PAD, y);
    y += 2;
    setDraw(SECONDARY);
    doc.line(PAD, y, PAD + 34, y);
    y += 6;

    setFill(LIGHTGRAY);
    const summaryText  = data.summaries.map((s) => s.flash).join(' ');
    const summaryLines = doc.splitTextToSize(summaryText, W - PAD * 2 - 6) as string[];
    const boxH         = summaryLines.length * 4.5 + 6;
    checkY(boxH);
    doc.roundedRect(PAD, y - 3, W - PAD * 2, boxH, 2, 2, 'F');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    setColor(GRAY);
    summaryLines.forEach((line, i) => text(line, PAD + 3, y + i * 4.5 + 1));
    y += boxH + 6;
  }

  // Q&A
  if (messages.length > 0) {
    checkY(10);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    setColor(PRIMARY);
    text('Chat Q&A', PAD, y);
    y += 2;
    setDraw(SECONDARY);
    doc.line(PAD, y, PAD + 26, y);
    y += 6;

    const pairs: { q: string; a: string }[] = [];
    for (let i = 0; i < messages.length - 1; i += 2) {
      if (messages[i].from === 'user' && messages[i + 1]?.from === 'ai') {
        pairs.push({ q: messages[i].text, a: messages[i + 1].text });
      }
    }

    pairs.forEach(({ q, a }) => {
      const qLines = doc.splitTextToSize(`Q: ${q}`, W - PAD * 2 - 4) as string[];
      checkY(qLines.length * 4.5 + 3);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      setColor(SECONDARY);
      qLines.forEach((line, i) => text(line, PAD, y + i * 4.5));
      y += qLines.length * 4.5 + 2;

      const aLines = doc.splitTextToSize(`A: ${a}`, W - PAD * 2 - 4) as string[];
      checkY(aLines.length * 4.5 + 4);
      doc.setFont('helvetica', 'normal');
      setColor(GRAY);
      aLines.forEach((line, i) => text(line, PAD, y + i * 4.5));
      y += aLines.length * 4.5 + 5;
    });
  }

  // FOOTER
  const totalPages = (doc as any).internal.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    setFill([248, 250, 252]);
    doc.rect(0, 285, W, 12, 'F');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    setColor(GRAY);
    text('Generated by UseWise \u2014 usewise.app', PAD, 291);
    text(`Page ${p} / ${totalPages}`, W - PAD, 291, { align: 'right' });
  }

  doc.save('usewise-report.pdf');
}