"""Generate a read-only vertical bracket preview for the home page."""

import json


def generate_vertical_bracket(r32_matchups, results, team_flags, confirmed_teams,
                              r16_matchups=None, qf_matchups=None, sf_matchups=None, final_matchups=None,
                              third_place_matchups=None, match_dates=None):
    """Render an interactive vertical bracket using ESPN's actual draw for all rounds."""
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
    r16_json = json.dumps(r16_matchups or [])
    qf_json = json.dumps(qf_matchups or [])
    sf_json = json.dumps(sf_matchups or [])
    final_json = json.dumps(final_matchups or [])
    third_place_json = json.dumps(third_place_matchups or [])
    dates_json = json.dumps(match_dates or {})
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
    align-items: stretch;
    gap: 0.4rem;
}}
.matchup {{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
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
.team-row[style*="cursor: pointer"]:hover {{
    background: rgba(255,215,0,0.08);
    border-radius: 4px;
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
.match-date {{
    font-size: 0.55rem;
    color: rgba(255,215,0,0.6);
    text-align: center;
    padding: 0.15rem 0 0 0;
    border-top: 1px solid rgba(41,181,232,0.1);
    letter-spacing: 0.5px;
}}
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
    var espnR16 = {r16_json};
    var espnQF = {qf_json};
    var espnSF = {sf_json};
    var espnFinal = {final_json};
    var espnThirdPlace = {third_place_json};
    var matchDates = {dates_json};
    var played = {played_json};
    var flags = {flags_json};
    var confirmed = new Set({confirmed_json});
    var bracket = document.getElementById("vbracket");

    function getFlag(t) {{ return flags[t] || ""; }}
    function isTbd(t) {{ return t === "TBD"; }}
    function getResult(t1, t2) {{
        if (isTbd(t1) || isTbd(t2)) return null;
        return played[t1 + "|" + t2] || played[t2 + "|" + t1] || null;
    }}

    // picks[0..15] = R32 winners, picks[16..23] = R16, picks[24..27] = QF, picks[28..29] = SF, picks[30] = final, picks[31] = 3rd place
    var picks = new Array(32).fill(null);

    // Load saved picks from localStorage
    try {{
        var saved = localStorage.getItem("vb_picks");
        if (saved) {{
            var arr = JSON.parse(saved);
            for (var i = 0; i < arr.length && i < 32; i++) picks[i] = arr[i];
        }}
    }} catch(e) {{}}

    // Pre-fill locked results into picks (overrides saved for locked matches)
    // R32
    for (var i = 0; i < matchups.length; i++) {{
        var r = getResult(matchups[i][0], matchups[i][1]);
        if (r && r.winner) picks[i] = r.winner;
    }}
    // R16+: use ESPN matchups directly for pre-fill
    for (var i = 0; i < espnR16.length; i++) {{
        var t1 = espnR16[i][0], t2 = espnR16[i][1];
        if (t1 && t2 && t1 !== "TBD" && t2 !== "TBD") {{
            var r = getResult(t1, t2);
            if (r && r.winner) picks[16 + i] = r.winner;
        }}
    }}
    for (var i = 0; i < espnQF.length; i++) {{
        var t1 = espnQF[i][0], t2 = espnQF[i][1];
        if (t1 && t2 && t1 !== "TBD" && t2 !== "TBD") {{
            var r = getResult(t1, t2);
            if (r && r.winner) picks[24 + i] = r.winner;
        }}
    }}
    for (var i = 0; i < espnSF.length; i++) {{
        var t1 = espnSF[i][0], t2 = espnSF[i][1];
        if (t1 && t2 && t1 !== "TBD" && t2 !== "TBD") {{
            var r = getResult(t1, t2);
            if (r && r.winner) picks[28 + i] = r.winner;
        }}
    }}
    if (espnFinal.length > 0) {{
        var t1 = espnFinal[0][0], t2 = espnFinal[0][1];
        if (t1 && t2 && t1 !== "TBD" && t2 !== "TBD") {{
            var r = getResult(t1, t2);
            if (r && r.winner) picks[30] = r.winner;
        }}
    }}
    if (espnThirdPlace.length > 0) {{
        var t1 = espnThirdPlace[0][0], t2 = espnThirdPlace[0][1];
        if (t1 && t2 && t1 !== "TBD" && t2 !== "TBD") {{
            var r = getResult(t1, t2);
            if (r && r.winner) picks[31] = r.winner;
        }}
    }}

    savePicks();

    function savePicks() {{
        try {{ localStorage.setItem("vb_picks", JSON.stringify(picks)); }} catch(e) {{}}
    }}

    function pickTeam(idx, team) {{
        var old = picks[idx];
        if (old === team) return;
        // Clear downstream picks that depended on the old value
        if (old) {{
            for (var j = idx + 1; j < 32; j++) {{
                if (picks[j] === old) picks[j] = null;
            }}
        }}
        picks[idx] = team;
        savePicks();
        renderAll();
    }}

    function renderAll() {{
        bracket.innerHTML = "";

        // R32: only show if not all matches are played
        var r32AllPlayed = matchups.every(function(m) {{ return !!getResult(m[0], m[1]); }});
        if (!r32AllPlayed) {{
            addRoundLabel("Round of 32");
            var r32Row = addRoundRow();
            for (var i = 0; i < matchups.length; i++) {{
                r32Row.appendChild(createMatchup(matchups[i][0], matchups[i][1], i, (matchDates.r32||[])[i]||""));
            }}
        }}

        // R16: ESPN matchups (hide if all played)
        var r16AllPlayed = espnR16.length > 0 && espnR16.every(function(m) {{
            var t1 = m[0] || "TBD", t2 = m[1] || "TBD";
            return t1 !== "TBD" && t2 !== "TBD" && !!getResult(t1, t2);
        }});
        if (!r16AllPlayed) {{
            addRoundLabel("Round of 16");
            var r16Row = addRoundRow();
            for (var i = 0; i < espnR16.length; i++) {{
                var t1 = espnR16[i][0] || "TBD";
                var t2 = espnR16[i][1] || "TBD";
                r16Row.appendChild(createMatchup(t1, t2, 16 + i, (matchDates.r16||[])[i]||""));
            }}
        }}

        // QF
        addRoundLabel("Quarter-finals");
        var qfRow = addRoundRow();
        for (var i = 0; i < espnQF.length; i++) {{
            var t1 = espnQF[i][0] || "TBD";
            var t2 = espnQF[i][1] || "TBD";
            qfRow.appendChild(createMatchup(t1, t2, 24 + i, (matchDates.qf||[])[i]||""));
        }}

        // SF
        addRoundLabel("Semi-finals");
        var sfRow = addRoundRow();
        for (var i = 0; i < espnSF.length; i++) {{
            var t1 = espnSF[i][0] || "TBD";
            var t2 = espnSF[i][1] || "TBD";
            sfRow.appendChild(createMatchup(t1, t2, 28 + i, (matchDates.sf||[])[i]||""));
        }}

        // 3rd Place (Jul 18 — before Final)
        if (espnThirdPlace.length > 0) {{
            addRoundLabel("3rd Place");
            var tpRow = addRoundRow();
            var tp1 = espnThirdPlace[0][0] || "TBD";
            var tp2 = espnThirdPlace[0][1] || "TBD";
            tpRow.appendChild(createMatchup(tp1, tp2, 31, (matchDates["3rd_place"]||[])[0]||""));
        }}

        // Final
        addRoundLabel("Final");
        var fRow = addRoundRow();
        var ft1 = espnFinal.length > 0 ? (espnFinal[0][0] || "TBD") : "TBD";
        var ft2 = espnFinal.length > 0 ? (espnFinal[0][1] || "TBD") : "TBD";
        fRow.appendChild(createMatchup(ft1, ft2, 30, (matchDates.final||[])[0]||""));

        // Champion
        if (picks[30]) {{
            var cd = document.createElement("div");
            cd.style.cssText = "text-align:center;margin:0.5rem 0;padding:0.5rem;background:linear-gradient(135deg,rgba(17,86,117,0.5),rgba(13,61,82,0.7));border:2px solid #FFD700;border-radius:10px;";
            cd.innerHTML = '<span style="font-size:1.5rem;">' + getFlag(picks[30]) + '</span><br><span style="font-size:0.85rem;font-weight:800;color:#FFD700;">🏆 ' + picks[30] + '</span>';
            bracket.appendChild(cd);
        }}
    }}

    function addRoundLabel(text) {{
        var lbl = document.createElement("div");
        lbl.className = "round-label";
        lbl.textContent = text;
        bracket.appendChild(lbl);
    }}
    function addRoundRow() {{
        var row = document.createElement("div");
        row.className = "round";
        bracket.appendChild(row);
        return row;
    }}

    // Override createMatchup to accept pickIdx for cascading
    function createMatchup(t1, t2, pickIdx, dateStr) {{
        var result = getResult(t1, t2);
        var locked = !!result;
        var m = document.createElement("div");
        m.className = "matchup" + (locked ? " played" : "");

        function makeRow(team, isT1) {{
            var row = document.createElement("div");
            row.className = "team-row";
            var cls = "name";
            var scoreHtml = "";
            if (isTbd(team)) {{
                cls = "name tbd";
            }} else if (locked) {{
                if (result.winner === team) {{
                    cls = "name winner";
                    var parts = result.score.split("-");
                    scoreHtml = '<span class="score winner">' + (isT1 ? parts[0] : parts[1]) + '</span>';
                }} else {{
                    cls = "name loser";
                    var parts = result.score.split("-");
                    scoreHtml = '<span class="score">' + (isT1 ? parts[0] : parts[1]) + '</span>';
                }}
            }} else if (picks[pickIdx] === team) {{
                cls = "name winner";
            }}
            var display = isTbd(team) ? "TBD" : (team.length > 13 ? team.substring(0,12) + "\u2026" : team);
            row.innerHTML = '<span class="flag">' + (isTbd(team) ? "" : getFlag(team)) + '</span>' +
                '<span class="' + cls + '">' + display + '</span>' + scoreHtml;
            if (!locked && !isTbd(team)) {{
                row.style.cursor = "pointer";
                row.addEventListener("click", function() {{ pickTeam(pickIdx, team); }});
            }}
            return row;
        }}

        m.appendChild(makeRow(t1, true));
        m.appendChild(makeRow(t2, false));
        // Always add date row for consistent card height
        var dd = document.createElement("div");
        dd.className = "match-date";
        dd.textContent = dateStr || "\u00A0";
        if (!dateStr) dd.style.visibility = "hidden";
        m.appendChild(dd);
        return m;
    }}

    renderAll();
}})();
</script>
</body>
</html>'''
    return html
