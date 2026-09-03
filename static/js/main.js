// Barani Payroll Interactive JS Helper

document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Client-side real-time calculation preview for payroll table inputs
    const payrollTable = document.getElementById("interactive-payroll-table");
    if (payrollTable) {
        payrollTable.addEventListener("input", function (e) {
            if (
                e.target.classList.contains("calc-trigger")
            ) {
                recalculateRow(e.target.closest("tr"));
                recalculateGrandTotals();
            }
        });
    }

    function recalculateRow(row) {
        const standardDays = parseFloat(document.getElementById("standard_days_val")?.value || 26.0);
        const otRate = parseFloat(document.getElementById("ot_rate_val")?.value || 56.25);

        const basicFixed = parseFloat(row.dataset.basic || 0);
        const daFixed = parseFloat(row.dataset.da || 0);
        const hraFixed = parseFloat(row.dataset.hra || 0);
        const washingFixed = parseFloat(row.dataset.washing || 0);
        const convFixed = parseFloat(row.dataset.conv || 0);
        const specialFixed = parseFloat(row.dataset.special || 0);
        const stipendFixed = parseFloat(row.dataset.stipend || 0);
        const pfEligible = row.dataset.pfEligible === "1" || row.dataset.pfEligible === "true";
        const esiEligible = row.dataset.esiEligible === "1" || row.dataset.esiEligible === "true";

        const workingDaysInput = row.querySelector(".input-wdays");
        const otHoursInput = row.querySelector(".input-othours");
        const otherDedInput = row.querySelector(".input-otherded");

        const wDays = parseFloat(workingDaysInput?.value || 0);
        const otHours = parseFloat(otHoursInput?.value || 0);
        const otherDed = parseFloat(otherDedInput?.value || 0);

        const proRate = (val) => (val > 0 && wDays > 0 ? (val / standardDays) * wDays : 0.0);

        let gross = 0.0;
        let pf = 0.0;
        let esi = 0.0;
        let otAmount = Math.round(otHours * otRate * 100) / 100;

        if (stipendFixed > 0) {
            // NAPS Calculation
            const stipendEarned = proRate(stipendFixed);
            gross = Math.round((stipendEarned + otAmount) * 100) / 100;
            if (pfEligible && stipendEarned > 0) {
                pf = Math.round(Math.min(stipendEarned * 0.12, 1800.0) * 100) / 100;
            }
            if (esiEligible && gross > 0 && gross <= 21000.0) {
                esi = Math.round(gross * 0.0175 * 100) / 100;
            }
        } else {
            // Staff Calculation
            const bEarned = proRate(basicFixed);
            const daEarned = proRate(daFixed);
            const hEarned = proRate(hraFixed);
            const wEarned = proRate(washingFixed);
            const cEarned = proRate(convFixed);
            const sEarned = proRate(specialFixed);

            gross = Math.round((bEarned + daEarned + hEarned + wEarned + cEarned + sEarned + otAmount) * 100) / 100;
            if (pfEligible && (bEarned + daEarned) > 0) {
                pf = Math.round(Math.min((bEarned + daEarned) * 0.12, 1800.0) * 100) / 100;
            }
            if (esiEligible && gross > 0 && gross <= 21000.0) {
                esi = Math.round(gross * 0.0175 * 100) / 100;
            }
        }

        const totalDed = Math.round((pf + esi + otherDed) * 100) / 100;
        const net = Math.round((gross - totalDed) * 100) / 100;

        // Update DOM row cells if present
        const cellOt = row.querySelector(".cell-ot");
        const cellGross = row.querySelector(".cell-gross");
        const cellPf = row.querySelector(".cell-pf");
        const cellEsi = row.querySelector(".cell-esi");
        const cellTotalDed = row.querySelector(".cell-totalded");
        const cellNet = row.querySelector(".cell-net");

        if (cellOt) cellOt.textContent = "₹" + otAmount.toFixed(2);
        if (cellGross) cellGross.textContent = "₹" + gross.toFixed(2);
        if (cellPf) cellPf.textContent = "₹" + pf.toFixed(2);
        if (cellEsi) cellEsi.textContent = "₹" + esi.toFixed(2);
        if (cellTotalDed) cellTotalDed.textContent = "₹" + totalDed.toFixed(2);
        if (cellNet) cellNet.textContent = "₹" + net.toFixed(2);
    }

    function recalculateGrandTotals() {
        let grandGross = 0;
        let grandOt = 0;
        let grandPf = 0;
        let grandEsi = 0;
        let grandDed = 0;
        let grandNet = 0;

        const rows = payrollTable.querySelectorAll("tbody tr");
        rows.forEach((row) => {
            const grossText = row.querySelector(".cell-gross")?.textContent.replace("₹", "") || "0";
            const otText = row.querySelector(".cell-ot")?.textContent.replace("₹", "") || "0";
            const pfText = row.querySelector(".cell-pf")?.textContent.replace("₹", "") || "0";
            const esiText = row.querySelector(".cell-esi")?.textContent.replace("₹", "") || "0";
            const dedText = row.querySelector(".cell-totalded")?.textContent.replace("₹", "") || "0";
            const netText = row.querySelector(".cell-net")?.textContent.replace("₹", "") || "0";

            grandGross += parseFloat(grossText) || 0;
            grandOt += parseFloat(otText) || 0;
            grandPf += parseFloat(pfText) || 0;
            grandEsi += parseFloat(esiText) || 0;
            grandDed += parseFloat(dedText) || 0;
            grandNet += parseFloat(netText) || 0;
        });

        const elGross = document.getElementById("stat-total-gross");
        const elOt = document.getElementById("stat-total-ot");
        const elPf = document.getElementById("stat-total-pf");
        const elEsi = document.getElementById("stat-total-esi");
        const elDed = document.getElementById("stat-total-ded");
        const elNet = document.getElementById("stat-total-net");

        if (elGross) elGross.textContent = "₹" + grandGross.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (elOt) elOt.textContent = "₹" + grandOt.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (elPf) elPf.textContent = "₹" + grandPf.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (elEsi) elEsi.textContent = "₹" + grandEsi.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (elDed) elDed.textContent = "₹" + grandDed.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (elNet) elNet.textContent = "₹" + grandNet.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
});
