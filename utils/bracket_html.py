"""Generate interactive HTML bracket with direct click-to-advance."""

import json


def generate_interactive_bracket(
    r32_matchups: list,
    locked_winners: dict,
    current_picks: list,
    team_flags: dict,
    team_list: list,
) -> str:
    """
    Render interactive bracket. Seeds on left (click to pick R32 winner),
    then each subsequent round shows 2 teams per matchup — click one to advance.
    No popup overlay needed.
    """
    matchups_json = json.dumps(r32_matchups)
    locked_json = json.dumps({f"{k[0]}|{k[1]}": v for k, v in locked_winners.items()})
    picks_json = json.dumps(current_picks)
    flags_json = json.dumps(team_flags)
    team_list_json = json.dumps(team_list)

    html = f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: rgba(17, 86, 117, 0.12);
    overflow-x: auto;
    overflow-y: hidden;
    border-radius: 14px;
}}
.bracket-wrap {{
    position: relative;
    min-width: 1300px;
    height: 1020px;
    padding: 15px 20px;
}}
.node {{
    position: absolute;
    width: 140px;
    height: 28px;
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 0 8px;
    background: rgba(17, 86, 117, 0.45);
    border: 1px solid rgba(41, 181, 232, 0.3);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    user-select: none;
}}
.node:hover {{
    background: rgba(41, 181, 232, 0.35);
    border-color: rgba(41, 181, 232, 0.7);
    transform: scale(1.04);
    box-shadow: 0 2px 10px rgba(41, 181, 232, 0.3);
    z-index: 10;
}}
.node.winner {{
    background: rgba(17, 86, 117, 0.7);
    border-color: #FFD700;
    box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}}
.node.winner .name {{ color: #FFD700; }}
.node.locked {{
    cursor: default;
}}
.node.locked:hover {{
    transform: none;
    box-shadow: none;
    background: rgba(17, 86, 117, 0.45);
    border-color: rgba(41, 181, 232, 0.3);
}}
.node.locked.winner {{
    background: rgba(17, 86, 117, 0.7);
    border-color: #FFD700;
    box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}}
.node.locked.winner:hover {{
    background: rgba(17, 86, 117, 0.7);
    box-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}}
.node.tbd {{
    opacity: 0.4;
    cursor: default;
}}
.node.tbd:hover {{
    transform: none;
    box-shadow: none;
    background: rgba(17, 86, 117, 0.45);
    border-color: rgba(41, 181, 232, 0.3);
}}
.node.champion {{
    border: 2px solid #FFD700;
    background: linear-gradient(135deg, #115675, #0d3d52);
    box-shadow: 0 0 18px rgba(255, 215, 0, 0.4);
    width: 150px;
    height: 34px;
}}
.node.champion .name {{ color: #FFD700; font-weight: 800; font-size: 0.78rem; }}
.node .flag {{ font-size: 0.8rem; flex-shrink: 0; }}
.node .name {{
    font-size: 0.7rem;
    font-weight: 600;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.node .lock {{ font-size: 0.55rem; margin-left: auto; opacity: 0.7; }}
.round-label {{
    position: absolute;
    font-size: 0.6rem;
    font-weight: 700;
    color: #29B5E8;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.8;
}}
</style>
</head>
<body>
<div class="bracket-wrap" id="bracket-root">
    <svg id="lines-svg" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:0;"></svg>
</div>

<script>
(function() {{
    var r32Matchups = {matchups_json};
    var lockedWinners = {locked_json};
    var picks = {picks_json};
    var flags = {flags_json};
    var teamList = {team_list_json};

    while (picks.length < 31) picks.push(null);

    // Layout
    var H = 1000, TOP_PAD = 35, LEFT_PAD = 20;
    var SEED_W = 135, NODE_W = 145, NODE_H = 30, PAIR_GAP = 4;
    var COL_POSITIONS = [LEFT_PAD, 180, 370, 560, 750, 950];
    // Cols: 0=Seeds(32), 1=R32 winners shown as pairs feeding R16(16 nodes as 8 pairs), etc.
    // Actually: Seeds=32 nodes, then R16=16 nodes as 8 matchup pairs, QF=8 as 4 pairs, SF=4 as 2, Final=2 as 1

    // New approach:
    // Col 0: 32 seed nodes (16 matchup pairs, 2 per matchup) -- CLICK to pick R32 winner
    // Col 1: 16 R32 winner nodes shown as 8 matchup pairs -- CLICK to pick R16 winner  
    // Col 2: 8 R16 winner nodes as 4 pairs -- CLICK to pick QF winner
    // Col 3: 4 QF winners as 2 pairs -- CLICK to pick SF winner
    // Col 4: 2 SF winners as 1 pair -- CLICK to pick champion
    // Col 5: 1 champion node

    var roundLabels = ["R32", "R16", "QF", "SF", "FINAL", ""];

    function getFlag(team) {{ return flags[team] || ""; }}
    function isLocked(t1, t2) {{
        if (!t1 || !t2) return null;
        return lockedWinners[t1 + "|" + t2] || lockedWinners[t2 + "|" + t1] || null;
    }}

    function getPairYPositions(numPairs, nodeH) {{
        // Each pair = 2 nodes stacked with PAIR_GAP between them
        // Distribute pairs evenly with breathing room between matchups
        var totalH = H - 2 * TOP_PAD;
        var pairHeight = nodeH * 2 + PAIR_GAP;
        var matchupGap = (totalH - numPairs * pairHeight) / (numPairs + 1);
        if (matchupGap < 4) matchupGap = 4;
        var positions = [];
        for (var i = 0; i < numPairs; i++) {{
            var topY = TOP_PAD + matchupGap + i * (pairHeight + matchupGap);
            positions.push([topY, topY + nodeH + PAIR_GAP]);
        }}
        return positions;
    }}

    // Y positions for each column
    var col0Y = getPairYPositions(16, NODE_H); // 16 pairs of 2 = 32 seeds
    var col1Y = getPairYPositions(8, NODE_H);  // 8 pairs of 2 = 16 R32 winners
    var col2Y = getPairYPositions(4, NODE_H);  // 4 pairs
    var col3Y = getPairYPositions(2, NODE_H);  // 2 pairs
    var col4Y = getPairYPositions(1, NODE_H);  // 1 pair
    var col5Y = [[(H/2 - NODE_H/2 - 2), null]]; // champion single node

    var allColY = [col0Y, col1Y, col2Y, col3Y, col4Y, col5Y];

    function getPickOffset(col) {{
        // col 0: picks[0-15] (R32 winners)
        // col 1: picks[16-23] (R16 winners)
        // col 2: picks[24-27] (QF winners)
        // col 3: picks[28-29] (SF winners)
        // col 4: picks[30] (champion)
        if (col === 0) return 0;
        if (col === 1) return 16;
        if (col === 2) return 24;
        if (col === 3) return 28;
        if (col === 4) return 30;
        return 31;
    }}

    function clearDownstream(fromIdx) {{
        var nextIdx;
        if (fromIdx < 16) nextIdx = 16 + Math.floor(fromIdx / 2);
        else if (fromIdx < 24) nextIdx = 24 + Math.floor((fromIdx - 16) / 2);
        else if (fromIdx < 28) nextIdx = 28 + Math.floor((fromIdx - 24) / 2);
        else if (fromIdx < 30) nextIdx = 30;
        else return;
        if (picks[nextIdx]) {{
            picks[nextIdx] = null;
            clearDownstream(nextIdx);
        }}
    }}

    function prefillLocked() {{
        // R32
        for (var i = 0; i < 16; i++) {{
            var m = r32Matchups[i];
            var locked = isLocked(m[0], m[1]);
            if (locked && !picks[i]) picks[i] = locked;
        }}
        // R16 and beyond
        for (var col = 1; col <= 4; col++) {{
            var numPairs = allColY[col].length;
            var offset = getPickOffset(col);
            for (var p = 0; p < numPairs; p++) {{
                var t1Idx, t2Idx;
                if (col === 1) {{ t1Idx = p*2; t2Idx = p*2+1; }}
                else if (col === 2) {{ t1Idx = 16+p*2; t2Idx = 16+p*2+1; }}
                else if (col === 3) {{ t1Idx = 24+p*2; t2Idx = 24+p*2+1; }}
                else if (col === 4) {{ t1Idx = 28; t2Idx = 29; }}
                var t1 = picks[t1Idx], t2 = picks[t2Idx];
                if (t1 && t2) {{
                    var locked = isLocked(t1, t2);
                    if (locked && !picks[offset + p]) picks[offset + p] = locked;
                }}
            }}
        }}
    }}

    function syncState() {{
        var encoded = picks.map(function(p) {{
            if (!p) return "_";
            var idx = teamList.indexOf(p);
            return idx >= 0 ? String(idx) : p;
        }}).join(",");
        var url = new URL(window.parent.location);
        url.searchParams.set("b", encoded);
        window.parent.history.replaceState(null, "", url.toString());
    }}

    function pickTeam(pickIdx, team) {{
        if (picks[pickIdx] === team) return; // already picked
        picks[pickIdx] = team;
        clearDownstream(pickIdx);
        render();
        syncState();
    }}

    function render() {{
        var root = document.getElementById("bracket-root");
        var svg = document.getElementById("lines-svg");
        root.querySelectorAll(".node, .round-label").forEach(function(el) {{ el.remove(); }});
        var lines = [];

        // Labels
        var labels = ["R32", "R16", "QF", "SF", "FINAL", "CHAMPION"];
        for (var c = 0; c < 6; c++) {{
            var lbl = document.createElement("div");
            lbl.className = "round-label";
            lbl.style.left = (COL_POSITIONS[c] + (c === 0 ? SEED_W : NODE_W) / 2 - 15) + "px";
            lbl.style.top = "8px";
            lbl.textContent = labels[c];
            root.appendChild(lbl);
        }}

        // Col 0: Seeds (32 teams in 16 pairs) — click to set R32 winner
        for (var p = 0; p < 16; p++) {{
            var t1 = r32Matchups[p][0];
            var t2 = r32Matchups[p][1];
            var winner = picks[p];
            var locked = isLocked(t1, t2);
            var ys = col0Y[p];

            for (var ti = 0; ti < 2; ti++) {{
                var team = ti === 0 ? t1 : t2;
                var y = ys[ti];
                var node = document.createElement("div");
                node.className = "node";
                node.style.left = COL_POSITIONS[0] + "px";
                node.style.top = y + "px";
                node.style.width = SEED_W + "px";

                if (team === winner) node.classList.add("winner");
                if (locked) node.classList.add("locked");

                var flagHtml = team ? '<span class="flag">' + getFlag(team) + '</span>' : '';
                var nameText = team || "TBD";
                if (nameText.length > 13) nameText = nameText.substring(0, 12) + "...";
                var lockIcon = (locked && team === winner) ? '<span class="lock">&#10004;</span>' : '';
                node.innerHTML = flagHtml + '<span class="name">' + nameText + '</span>' + lockIcon;

                if (!locked && team) {{
                    (function(pickIdx, t) {{
                        node.addEventListener("click", function(e) {{
                            e.stopPropagation();
                            pickTeam(pickIdx, t);
                        }});
                    }})(p, team);
                }}
                root.appendChild(node);

                // Connector from seed to R16 pair slot
                if (team === winner && winner) {{
                    var startX = COL_POSITIONS[0] + SEED_W;
                    var startY = y + NODE_H / 2;
                    // Connects to col1 pair position
                    var targetPair = Math.floor(p / 2);
                    var targetSlotInPair = p % 2;
                    var endX = COL_POSITIONS[1];
                    var endY = col1Y[targetPair][targetSlotInPair] + NODE_H / 2;
                    var midX = startX + (endX - startX) / 2;
                    lines.push('<path d="M ' + startX + ' ' + startY + ' L ' + midX + ' ' + startY + ' L ' + midX + ' ' + endY + ' L ' + endX + ' ' + endY + '" fill="none" stroke="rgba(255,215,0,0.5)" stroke-width="2"/>');
                }}
            }}
        }}

        // Cols 1-4: Matchup pairs — show two feeder teams, click to pick winner
        for (var col = 1; col <= 4; col++) {{
            var numPairs = allColY[col].length;
            var offset = getPickOffset(col);
            var pairYs = allColY[col];

            for (var p = 0; p < numPairs; p++) {{
                // Get the two teams feeding this matchup
                var t1, t2;
                if (col === 1) {{ t1 = picks[p*2]; t2 = picks[p*2+1]; }}
                else if (col === 2) {{ t1 = picks[16+p*2]; t2 = picks[16+p*2+1]; }}
                else if (col === 3) {{ t1 = picks[24+p*2]; t2 = picks[24+p*2+1]; }}
                else if (col === 4) {{ t1 = picks[28]; t2 = picks[29]; }}

                var winner = picks[offset + p];
                var locked = (t1 && t2) ? isLocked(t1, t2) : null;
                var ys = pairYs[p];

                for (var ti = 0; ti < 2; ti++) {{
                    var team = ti === 0 ? t1 : t2;
                    var y = ys[ti];
                    var node = document.createElement("div");
                    node.className = "node";
                    node.style.left = COL_POSITIONS[col] + "px";
                    node.style.top = y + "px";

                    if (!team) {{
                        node.classList.add("tbd");
                    }} else if (team === winner) {{
                        node.classList.add("winner");
                        if (locked) node.classList.add("locked");
                    }} else if (locked) {{
                        node.classList.add("locked");
                    }}

                    var flagHtml = team ? '<span class="flag">' + getFlag(team) + '</span>' : '';
                    var nameText = team || "TBD";
                    if (nameText.length > 14) nameText = nameText.substring(0, 13) + "...";
                    var lockIcon = (locked && team === winner) ? '<span class="lock">&#10004;</span>' : '';
                    node.innerHTML = flagHtml + '<span class="name">' + nameText + '</span>' + lockIcon;

                    if (!locked && team) {{
                        (function(pickIdx, t) {{
                            node.addEventListener("click", function(e) {{
                                e.stopPropagation();
                                pickTeam(pickIdx, t);
                            }});
                        }})(offset + p, team);
                    }}
                    root.appendChild(node);

                    // Connector from winner to next col
                    if (team === winner && winner && col < 4) {{
                        var startX = COL_POSITIONS[col] + NODE_W;
                        var startY = y + NODE_H / 2;
                        var nextPair = Math.floor(p / 2);
                        var nextSlot = p % 2;
                        var endX = COL_POSITIONS[col + 1];
                        var endY = allColY[col + 1][nextPair][nextSlot] + NODE_H / 2;
                        var midX = startX + (endX - startX) / 2;
                        lines.push('<path d="M ' + startX + ' ' + startY + ' L ' + midX + ' ' + startY + ' L ' + midX + ' ' + endY + ' L ' + endX + ' ' + endY + '" fill="none" stroke="rgba(255,215,0,0.5)" stroke-width="2"/>');
                    }}
                }}
            }}
        }}

        // Col 5: Champion (single node)
        var champion = picks[30];
        if (champion) {{
            var y = col5Y[0][0];
            var node = document.createElement("div");
            node.className = "node champion";
            node.style.left = COL_POSITIONS[5] + "px";
            node.style.top = y + "px";
            node.innerHTML = '<span class="flag">' + getFlag(champion) + '</span><span class="name">&#127942; ' + champion + '</span>';
            root.appendChild(node);

            // Line from col4 winner to champion
            var sf1Y = col4Y[0][0], sf2Y = col4Y[0][1];
            var winnerY = (picks[28] === champion) ? sf1Y : sf2Y;
            var startX = COL_POSITIONS[4] + NODE_W;
            var startY = winnerY + NODE_H / 2;
            var endX = COL_POSITIONS[5];
            var endY = y + NODE_H / 2;
            var midX = startX + (endX - startX) / 2;
            lines.push('<path d="M ' + startX + ' ' + startY + ' L ' + midX + ' ' + startY + ' L ' + midX + ' ' + endY + ' L ' + endX + ' ' + endY + '" fill="none" stroke="rgba(255,215,0,0.7)" stroke-width="2.5"/>');
        }}

        svg.innerHTML = lines.join("");
    }}

    prefillLocked();
    render();
}})();
</script>
</body>
</html>'''
    return html
