document.addEventListener("DOMContentLoaded", function() {
  // Set report metadata
  const now = new Date();
  document.getElementById("report-date").textContent = now.toLocaleDateString('en-US', {
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  
  document.getElementById("report-id").textContent = 'RPT-' + now.getFullYear() + 
    (now.getMonth()+1).toString().padStart(2,'0') + 
    now.getDate().toString().padStart(2,'0') + '-' +
    now.getHours().toString().padStart(2,'0') + 
    now.getMinutes().toString().padStart(2,'0');

  // Load sample data (replace with your actual data loading)
  setTimeout(() => {
    const savedImage = localStorage.getItem('uploadedImage');
    if (savedImage) {
      document.getElementById('panel-image').src = savedImage;
    } else {
      document.getElementById('panel-image').src = 'img/sample-panel.jpg';
    }
    
    // Sample defects data
    document.getElementById('defects-container').innerHTML = `
      <div class="defect-card">
        <h6><i class="fas fa-fire text-danger me-2"></i>Hotspot (Severe)</h6>
        <p class="mb-1 small">Location: Right section (x: 72%, y: 58%)</p>
        <p class="mb-1 small">Temperature: 78°C (35°C above average)</p>
      </div>
      <div class="defect-card">
        <h6><i class="fas fa-cracked-egg text-warning me-2"></i>Micro-crack (Moderate)</h6>
        <p class="mb-1 small">Location: Lower left quadrant (x: 28%, y: 82%)</p>
        <p class="mb-1 small">Length: 3.2mm | Direction: 45°</p>
      </div>
    `;
    
    // Sample metrics
    document.getElementById('health-metrics').innerHTML = `
      <div class="metric-card">
        <h6><i class="fas fa-bolt text-primary me-2"></i>Performance Metrics</h6>
        <p class="mb-1 small">Current Efficiency: 82% of rated capacity</p>
        <p class="mb-1 small">Power Loss: 18% due to defects</p>
        <p class="mb-1 small">Estimated annual loss: $42.50</p>
      </div>
      <div class="metric-card">
        <h6><i class="fas fa-heartbeat text-info me-2"></i>Health Assessment</h6>
        <p class="mb-1 small">Overall Health Score: 6.8/10</p>
        <p class="mb-1 small">Predicted lifespan impact: 2.1 years</p>
      </div>
    `;
    
    // Sample technical analysis
    document.getElementById('technical-analysis').innerHTML = `
      <p>The analysis reveals two significant anomalies affecting panel performance:</p>
      <ol>
        <li>A severe hotspot in the right section indicating potential cell mismatch or partial shading.</li>
        <li>A moderate micro-crack in the lower left quadrant likely caused by mechanical stress.</li>
      </ol>
      <p>These defects collectively account for an estimated 18% reduction in power output and may accelerate degradation if left unaddressed.</p>
    `;
    
    // Sample recommendations
    document.getElementById('recommendations').innerHTML = `
      <ol>
        <li>Immediate investigation of the hotspot cause (check for shading, wiring issues, or cell mismatch).</li>
        <li>Professional repair of the micro-crack within 30 days to prevent propagation.</li>
        <li>Follow-up thermal imaging after 2 weeks to verify hotspot resolution.</li>
        <li>Consider replacing affected cells if performance doesn't improve by at least 15% post-repair.</li>
        <li>Quarterly inspections recommended for this panel due to identified vulnerabilities.</li>
      </ol>
    `;
  }, 500);

  // PDF Export Function
  document.getElementById("export-btn").addEventListener("click", exportToPDF);
});

async function exportToPDF() {
  const { jsPDF } = window.jspdf;
  const element = document.getElementById("report-content");
  const btn = document.getElementById("export-btn");
  const originalText = btn.innerHTML;

  try {
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Generating PDF...';
    btn.disabled = true;

    // Create a clone of the element to avoid affecting the original
    const elementClone = element.cloneNode(true);
    elementClone.style.position = "absolute";
    elementClone.style.left = "-9999px";
    document.body.appendChild(elementClone);

    const canvas = await html2canvas(elementClone, {
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true,
      scrollX: 0,
      scrollY: 0,
      backgroundColor: "#FFFFFF"
    });

    const pdf = new jsPDF({
      orientation: "portrait",
      unit: "mm",
      format: "a4"
    });

    // Calculate dimensions
    const imgWidth = 190; // A4 width (210mm) - 20mm margins
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    // Add image to PDF
    pdf.addImage(canvas.toDataURL("image/png"), "PNG", 10, 10, imgWidth, imgHeight);

    // Add footer
    const dateStr = document.getElementById("report-date").textContent;
    pdf.setFontSize(10);
    pdf.setTextColor(100);
    pdf.text(`Generated on ${dateStr}`, 10, pdf.internal.pageSize.getHeight() - 10);

    // Save the PDF
    pdf.save(`SolarPanelReport_${document.getElementById("report-id").textContent}.pdf`);

  } catch (error) {
    console.error("PDF Export Error:", error);
    showErrorToast("Failed to generate PDF. Please try again.");
  } finally {
    // Remove the cloned element
    if (elementClone) {
      document.body.removeChild(elementClone);
    }
    // Restore button state
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

function showErrorToast(message) {
  const toast = document.createElement("div");
  toast.className = "pdf-error-toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

