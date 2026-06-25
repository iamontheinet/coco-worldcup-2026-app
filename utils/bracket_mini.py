"""Generate a compact read-only mini bracket for the home page."""

import json


def generate_mini_bracket(r32_matchups, confirmed_teams, team_flags):
    """Render a compact read-only bracket showing R32 matchups (2 columns: seeds + projected R16 pairs)."""
    matchups_json = json.dumps(r32_matchups)
    confirmed_json = json.dumps(list(confirmed_teams or []))
    flags_json = json.dumps(team_flags)

    html = f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: transparent;
    overflow: hidden;
}}
.mini-bracket {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    padding: 0.5rem;
}}
.matchup {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(17, 86, 117, 0.3);
    border: 1px solid rgba(41, 181, 232, 0.2);
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
}}
.matchup.confirmed {{
    border-color: rgba(0, 200, 83, 0.5);
    box-shadow: 0 0 6px rgba(0, 200, 83, 0.15);
}}
.team {{
    display: flex;
    align-items: center;
    gap: 0.3rem;
    flex: 1;
}}
.team .flag {{ font-size: 0.9rem; }}
.team .name {{
    font-size: 0.75rem;
    font-weight: 600;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.team.qualified .name {{ color: #00e676; }}
.vs {{
    font-size: 0.65rem;
    color: rgba(255, 215, 0, 0.7);
    font-weight: 700;
    flex-shrink: 0;
}}
.match-num {{
    font-size: 0.55rem;
    color: rgba(41, 181, 232, 0.7);
    font-weight: 700;
    flex-shrink: 0;
    min-width: 1.2rem;
}}
</style>
</head>
<body>
<div class="mini-bracket" id="bracket-grid"></div>
<script>
(function() {{
    var matchups = {matchups_json};
    var confirmed = {confirmed_json};
    var flags = {flags_json};
    var grid = document.getElementById("bracket-grid");

    function isConfirmed(team) {{ return confirmed.indexOf(team) >= 0; }}
    function getFlag(team) {{ return flags[team] || ""; }}

    for (var i = 0; i < matchups.length; i++) {{
        var t1 = matchups[i][0];
        var t2 = matchups[i][1];
        var bothConfirmed = isConfirmed(t1) && isConfirmed(t2);

        var div = document.createElement("div");
        div.className = "matchup" + (bothConfirmed ? " confirmed" : "");

        var numSpan = '<span class="match-num">M' + (i + 1) + '</span>';
        var t1Class = isConfirmed(t1) ? "team qualified" : "team";
        var t2Class = isConfirmed(t2) ? "team qualified" : "team";
        var t1Name = t1.length > 14 ? t1.substring(0, 13) + "..." : t1;
        var t2Name = t2.length > 14 ? t2.substring(0, 13) + "..." : t2;

        div.innerHTML = numSpan +
            '<div class="' + t1Class + '"><span class="flag">' + getFlag(t1) + '</span><span class="name">' + t1Name + '</span></div>' +
            '<span class="vs">VS</span>' +
            '<div class="' + t2Class + '"><span class="flag">' + getFlag(t2) + '</span><span class="name">' + t2Name + '</span></div>';

        grid.appendChild(div);
    }}
}})();
</script>
</body>
</html>'''
    return html
