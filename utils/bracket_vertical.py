"""Generate a read-only vertical bracket preview for the home page."""

import json


def generate_vertical_bracket(r32_matchups, results, team_flags, confirmed_teams):
    """Render a vertical bracket: R32 → R16 → QF → SF → Final (top to bottom).

    Args:
        r32_matchups: list of 16 (team1, team2) tuples
        results: list of match result dicts (from get_all_results)
        team_flags: dict of team_name → flag emoji
        confirmed_teams: set of confirmed R32 team names
    """
    # Build lookup of played knockout results
    played = {}  # (t1, t2) → {"winner": str, "score": "1-0"}
    for r in results:
        t1, t2 = r["team_1_name"], r["team_2_name"]
        stage = r.get("stage", "")
        if stage != "Group Stage":
            winner = r.get("winner")
            if not winner:
                if r["team_1_score"] > r["team_2_score"]:
                    winner = t1
                elif r["team_2_score"] > r["team_1_score"]:
                    winner = t2
            played[(t1, t2)] = {
                "winner": winner,
                "score": f"{r['team_1_score']}-{r['team_2_score']}",
            }
            played[(t2, t1)] = {
                "winner": winner,
                "score": f"{r['team_2_score']}-{r['team_1_score']}",
            }

    matchups_json = json.dumps(r32_matchups)
    played_json = json.dumps({f"{k[0]}|{k[1]}": v for k, v in played.items()})
    flags_json = json.dumps(team_flags)
    confirmed_json = json.dumps(list(confirmed_teams or []))

    html = f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: transparent;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 0.5rem;
}}
.bracket {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.2rem;
}}
.round-label {{
    font-size: 0.7rem;
    color: rgba(255,215,0,0.8);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    text-align: center;
    margin: 0.2rem 0;
}}
.round {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.4rem;
}}
.matchup {{
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, rgba(17,86,117,0.45) 0%, rgba(13,61,82,0.65) 100%);
    border: 1px solid rgba(41,181,232,0.2);
    border-radius: 8px;
    padding: 0.35rem 0.5rem;
    min-width: 130px;
    max-width: 160px;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    transition: border-color 0.2s;
}}
.matchup.played {{
    border-color: rgba(0,200,83,0.4);
    box-shadow: 0 1px 6px rgba(0,200,83,0.1);
}}
.team-row {{
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0;
}}
.team-row + .team-row {{
    border-top: 1px solid rgba(41,181,232,0.12);
}}
.flag {{ font-size: 0.75rem; }}
.name {{
    font-size: 0.68rem;
    font-weight: 600;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}}
.name.winner {{ color: #FFD700; font-weight: 700; }}
.name.loser {{ color: rgba(255,255,255,0.4); }}
.name.tbd {{ color: rgba(255,255,255,0.3); font-style: italic; }}
.score {{
    font-size: 0.6rem;
    font-weight: 700;
    color: rgba(255,255,255,0.6);
    min-width: 1.2rem;
    text-align: right;
}}
.score.winner {{ color: #FFD700; }}
.connector-row {{
    display: flex;
    justify-content: center;
    gap: 0.4rem;
    padding: 0 0.5rem;
}}
.conn-line {{
    width: 1px;
    height: 12px;
    background: rgba(41,181,232,0.3);
}}
/* Responsive */
@media (max-width: 768px) {{
    .matchup {{ min-width: 110px; max-width: 140px; }}
    .name {{ font-size: 0.6rem; }}
    .round {{ gap: 0.3rem; }}
}}
@media (max-width: 480px) {{
    .matchup {{ min-width: 95px; max-width: 120px; padding: 0.25rem 0.35rem; }}
    .name {{ font-size: 0.55rem; }}
    .flag {{ font-size: 0.65rem; }}
}}
</style>
</head>
<body>
<div class="bracket" id="vbracket"></div>
<script>
(function() {{
    var matchups = {matchups_json};
    var played = {played_json};
    var flags = {flags_json};
    var confirmed = new Set({confirmed_json});
    var bracket = document.getElementById("vbracket");

    function getFlag(t) {{ return flags[t] || ""; }}
    function isTbd(t) {{ return t === "TBD"; }}
    function getResult(t1, t2) {{
        return played[t1 + "|" + t2] || played[t2 + "|" + t1] || null;
    }}

    function createMatchup(t1, t2) {{
        var result = getResult(t1, t2);
        var m = document.createElement("div");
        m.className = "matchup" + (result ? " played" : "");

        function teamRow(team, isT1) {{
            var cls = "name";
            var scoreCls = "score";
            var scoreText = "";
            if (isTbd(team)) {{
                cls = "name tbd";
            }} else if (result) {{
                if (result.winner === team) {{
                    cls = "name winner";
                    scoreCls = "score winner";
                }} else {{
                    cls = "name loser";
                }}
                var parts = result.score.split("-");
                scoreText = isT1 ? parts[0] : parts[1];
            }}
            var display = isTbd(team) ? "TBD" : (team.length > 13 ? team.substring(0,12) + "\u2026" : team);
            return '<div class="team-row">' +
                '<span class="flag">' + (isTbd(team) ? "" : getFlag(team)) + '</span>' +
                '<span class="' + cls + '">' + display + '</span>' +
                (scoreText ? '<span class="' + scoreCls + '">' + scoreText + '</span>' : '') +
                '</div>';
        }}
        m.innerHTML = teamRow(t1, true) + teamRow(t2, false);
        return m;
    }}

    function addRound(label, matchupList) {{
        var lbl = document.createElement("div");
        lbl.className = "round-label";
        lbl.textContent = label;
        bracket.appendChild(lbl);

        var row = document.createElement("div");
        row.className = "round";
        for (var i = 0; i < matchupList.length; i++) {{
            row.appendChild(createMatchup(matchupList[i][0], matchupList[i][1]));
        }}
        bracket.appendChild(row);
    }}

    // R32 (16 matchups)
    addRound("Round of 32", matchups);

    // Future rounds — show TBD placeholders based on R32 count
    var r16Count = Math.floor(matchups.length / 2);
    var r16 = [];
    for (var i = 0; i < r16Count; i++) {{
        // Check if we have a result for either R32 pair to fill R16
        var m1 = matchups[i * 2];
        var m2 = matchups[i * 2 + 1];
        var r1 = getResult(m1[0], m1[1]);
        var r2 = getResult(m2[0], m2[1]);
        var t1 = r1 ? r1.winner : "TBD";
        var t2 = r2 ? r2.winner : "TBD";
        r16.push([t1 || "TBD", t2 || "TBD"]);
    }}
    if (r16.length > 0) addRound("Round of 16", r16);

    // QF
    var qf = [];
    for (var i = 0; i < Math.floor(r16.length / 2); i++) {{
        var ra = getResult(r16[i*2][0], r16[i*2][1]);
        var rb = getResult(r16[i*2+1][0], r16[i*2+1][1]);
        qf.push([ra ? ra.winner || "TBD" : "TBD", rb ? rb.winner || "TBD" : "TBD"]);
    }}
    if (qf.length > 0) addRound("Quarter-finals", qf);

    // SF
    var sf = [];
    for (var i = 0; i < Math.floor(qf.length / 2); i++) {{
        var ra = getResult(qf[i*2][0], qf[i*2][1]);
        var rb = getResult(qf[i*2+1][0], qf[i*2+1][1]);
        sf.push([ra ? ra.winner || "TBD" : "TBD", rb ? rb.winner || "TBD" : "TBD"]);
    }}
    if (sf.length > 0) addRound("Semi-finals", sf);

    // Final
    if (sf.length >= 2) {{
        var ra = getResult(sf[0][0], sf[0][1]);
        var rb = getResult(sf[1][0], sf[1][1]);
        var finalMatch = [[ra ? ra.winner || "TBD" : "TBD", rb ? rb.winner || "TBD" : "TBD"]];
        addRound("Final", finalMatch);
    }}
}})();
</script>
</body>
</html>'''
    return html
