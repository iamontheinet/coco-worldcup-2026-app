"""Generate a compact bracket-tree visual for the home page R32 preview."""

import json


def generate_mini_bracket(r32_matchups, confirmed_teams, team_flags):
    """Render a bracket-tree showing R32 matchups with connecting lines to R16 slots."""
    matchups_json = json.dumps(r32_matchups)
    confirmed_json = json.dumps(list(confirmed_teams or []))
    flags_json = json.dumps(team_flags)
    num_matchups = len(r32_matchups)

    html = f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: transparent;
    overflow-x: auto;
    overflow-y: hidden;
}}
.bracket-container {{
    display: flex;
    align-items: stretch;
    justify-content: center;
    padding: 1rem 0.5rem;
    min-height: 100%;
    gap: 0;
}}
.round {{
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}}
.round-r32 {{
    gap: 0.35rem;
}}
.round-r16 {{
    gap: 0.35rem;
}}
.matchup {{
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, rgba(17,86,117,0.5) 0%, rgba(13,61,82,0.7) 100%);
    border: 1px solid rgba(41,181,232,0.25);
    border-radius: 8px;
    padding: 0.25rem 0.5rem;
    position: relative;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}}
.matchup.confirmed {{
    border-color: rgba(0,200,83,0.45);
    box-shadow: 0 1px 8px rgba(0,200,83,0.1);
}}
.team-row {{
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0;
}}
.team-row + .team-row {{
    border-top: 1px solid rgba(41,181,232,0.15);
}}
.flag {{ font-size: 0.8rem; }}
.name {{
    font-size: 0.7rem;
    font-weight: 600;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100px;
}}
.name.qualified {{ color: #00e676; }}
.name.tbd {{ color: rgba(255,255,255,0.3); font-style: italic; }}
.connector {{
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    width: 20px;
    position: relative;
}}
.conn-line {{
    position: absolute;
    border: 1px solid rgba(41,181,232,0.3);
    border-left: none;
}}
.r16-slot {{
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(17,86,117,0.2);
    border: 1px dashed rgba(41,181,232,0.2);
    border-radius: 6px;
    padding: 0.4rem 0.5rem;
    min-width: 50px;
}}
.r16-slot span {{
    font-size: 0.6rem;
    color: rgba(255,255,255,0.3);
    font-weight: 600;
}}
/* Mobile: single column */
@media (max-width: 768px) {{
    .bracket-container {{ flex-direction: column; align-items: stretch; }}
    .bracket-half {{ margin-bottom: 0.5rem; }}
    .connector, .round-r16 {{ display: none; }}
}}
.bracket-half {{
    display: flex;
    align-items: stretch;
}}
</style>
</head>
<body>
<div class="bracket-container" id="bracket"></div>
<script>
(function() {{
    var matchups = {matchups_json};
    var confirmed = new Set({confirmed_json});
    var flags = {flags_json};
    var container = document.getElementById("bracket");

    function getFlag(t) {{ return flags[t] || ""; }}
    function isConf(t) {{ return confirmed.has(t); }}
    function isTbd(t) {{ return t === "TBD"; }}

    function createMatchup(t1, t2, idx) {{
        var m = document.createElement("div");
        var bothConf = isConf(t1) && isConf(t2);
        m.className = "matchup" + (bothConf ? " confirmed" : "");

        function teamRow(t) {{
            var cls = isTbd(t) ? "name tbd" : (isConf(t) ? "name qualified" : "name");
            var display = isTbd(t) ? "TBD" : (t.length > 12 ? t.substring(0,11) + "\u2026" : t);
            return '<div class="team-row"><span class="flag">' + (isTbd(t) ? "" : getFlag(t)) + '</span><span class="' + cls + '">' + display + '</span></div>';
        }}
        m.innerHTML = teamRow(t1) + teamRow(t2);
        return m;
    }}

    // Split into two halves (top and bottom of bracket)
    var half = Math.ceil(matchups.length / 2);
    var topMatches = matchups.slice(0, half);
    var botMatches = matchups.slice(half);

    function buildHalf(matches, startIdx) {{
        var halfDiv = document.createElement("div");
        halfDiv.className = "bracket-half";

        var r32Col = document.createElement("div");
        r32Col.className = "round round-r32";

        for (var i = 0; i < matches.length; i++) {{
            r32Col.appendChild(createMatchup(matches[i][0], matches[i][1], startIdx + i));
        }}

        // Connector lines
        var connCol = document.createElement("div");
        connCol.className = "connector";
        connCol.style.height = "100%";

        // R16 placeholders
        var r16Col = document.createElement("div");
        r16Col.className = "round round-r16";
        var r16Count = Math.ceil(matches.length / 2);
        for (var j = 0; j < r16Count; j++) {{
            var slot = document.createElement("div");
            slot.className = "r16-slot";
            slot.innerHTML = '<span>R16</span>';
            r16Col.appendChild(slot);
        }}

        halfDiv.appendChild(r32Col);
        halfDiv.appendChild(connCol);
        halfDiv.appendChild(r16Col);
        return halfDiv;
    }}

    container.appendChild(buildHalf(topMatches, 0));
    container.appendChild(buildHalf(botMatches, half));
}})();
</script>
</body>
</html>'''
    return html
