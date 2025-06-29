function luminance(hex) {
    // Berechne Helligkeit für automatische Schriftfarbe
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0,2),16);
    const g = parseInt(hex.substring(2,4),16);
    const b = parseInt(hex.substring(4,6),16);
    return 0.299*r + 0.587*g + 0.114*b;
}
function textColor(bg) {
    return luminance(bg) > 160 ? "#222" : "#fff";
}

function renderMerkleTree(tree) {
    if (!tree || !tree.length) return;
    const svgWidth = 650;
    const levelHeight = 90;
    const radius = 27;

    // Root ist immer oben, Blätter unten: Farben werden von oben nach unten vergeben
    const levelColors = [
        "#e5f4fa",  // Blätter (unten, sehr helles Cyan)
        "#b8e5f8",  // ggf. weitere Zwischenebene
        "#6fc7ea",  // Cyan
        "#004372",  // Dunkelblau
        "#62ad37"   // Root (oben, grün)
    ];

    // ACHTUNG: tree[0] = Blätter, tree[tree.length-1] = Root
    const levelCount = tree.length;

    // Clean slate
    let svg = d3.select("#treevis").html('').append("svg")
        .attr("width", svgWidth)
        .attr("height", levelHeight * levelCount + 30);

    // Positionen berechnen, invertierte Y-Achse (Root oben)
    const nodePositions = [];
    for (let l = 0; l < levelCount; l++) {
        const y = (levelCount - l - 1) * levelHeight + 40;
        const level = tree[l];
        const n = level.length;
        const xStep = svgWidth / (n + 1);
        nodePositions.push(level.map((_, i) => ({
            x: xStep * (i + 1),
            y: y
        })));
    }

    // Kanten zeichnen (von Kindern zu Eltern)
    for (let l = 0; l < levelCount - 1; l++) {
        nodePositions[l].forEach((pos, i) => {
            const parentIdx = Math.floor(i / 2);
            const parentPos = nodePositions[l+1][parentIdx];
            svg.append("line")
                .attr("x1", pos.x)
                .attr("y1", pos.y - radius + 3)
                .attr("x2", parentPos.x)
                .attr("y2", parentPos.y + radius - 3)
                .attr("stroke", "#888")
                .attr("stroke-width", 3)
                .attr("opacity", 0.22);
        });
    }

    // Knoten zeichnen
    for (let l = 0; l < levelCount; l++) {
        const level = tree[l];
        level.forEach((hash, i) => {
            const {x, y} = nodePositions[l][i];
            // Farbindex: Blätter = 0, Root = highest
            const color = levelColors[l] || "#bbb";
            const fontColor = textColor(color);

            svg.append("circle")
                .attr("cx", x)
                .attr("cy", y)
                .attr("r", radius)
                .attr("fill", color)
                .attr("stroke", "#fff")
                .attr("stroke-width", 2)
                .on("mouseover", function() {
                    d3.select(this).attr("stroke", "#ffb200").attr("stroke-width", 4);
                    tooltip.style("display", "block").html(
                        `<div style='font-size:0.96em;max-width:330px;'>
                            <b>Full Hash:</b><br>
                            <span style='word-break:break-all;'>${hash}</span>
                        </div>`
                    );
                })
                .on("mousemove", function(e) {
                    tooltip.style("left", (e.pageX + 20) + "px")
                        .style("top", (e.pageY - 25) + "px");
                })
                .on("mouseout", function() {
                    d3.select(this).attr("stroke", "#fff").attr("stroke-width", 2);
                    tooltip.style("display", "none");
                });

            // Hash Label
            svg.append("text")
                .attr("x", x)
                .attr("y", y + 5)
                .attr("text-anchor", "middle")
                .attr("font-size", 13 + (l === levelCount - 1 ? 3 : 0))
                .attr("font-weight", l === levelCount - 1 ? "bold" : "normal")
                .attr("fill", fontColor)
                .text(hash.slice(0, 7) + "…");
        });
    }

    // Tooltip für vollständigen Hash
    d3.selectAll(".merkle-tooltip").remove(); // nur einen Tooltip!
    const tooltip = d3.select("body").append("div")
        .attr("class", "merkle-tooltip")
        .style("display", "none")
        .style("position", "absolute")
        .style("background", "#fff")
        .style("border", "1.5px solid #62ad37")
        .style("color", "#004372")
        .style("font-family", "Segoe UI,Arial,sans-serif")
        .style("font-size", "1em")
        .style("padding", "10px 13px")
        .style("border-radius", "9px")
        .style("box-shadow", "0 4px 18px #00437222");
}
