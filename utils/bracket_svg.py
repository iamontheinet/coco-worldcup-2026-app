"""Generate inline SVG for the tournament bracket visualization."""


def generate_bracket_svg(
    r32_matchups: list,
    r32_winners: list,
    r16_winners: list,
    qf_winners: list,
    sf_winners: list,
    champion,
    team_flags: dict,
) -> str:
    """Render a left-to-right tournament bracket as inline SVG."""

    # Layout constants
    W = 960
    H = 640
    NODE_W = 120
    NODE_H = 26
    ROUND_GAP = 180  # horizontal distance between rounds
    LEFT_PAD = 20
    TOP_PAD = 10

    # Rounds data: each round has N slots
    rounds = [
        r32_matchups,  # 16 matchups -> 32 team slots displayed as 16 winner slots
        r16_winners,   # 8
        qf_winners,    # 4
        sf_winners,    # 2
        [champion],    # 1
    ]

    # The R32 column shows the 16 winners (one per matchup)
    # Then R16 shows 8, QF 4, SF 2, Final 1
    round_counts = [16, 8, 4, 2, 1]
    round_labels = ["R32", "R16", "QF", "SF", "FINAL"]

    # Build winner lists for display
    r32_display = []
    for i, w in enumerate(r32_winners):
        if w:
            r32_display.append(w)
        else:
            r32_display.append(None)

    all_rounds = [r32_display, r16_winners, qf_winners, sf_winners, [champion]]

    def _label(team):
        if not team:
            return "TBD"
        flag = team_flags.get(team, "")
        short = team if len(team) <= 12 else team[:11] + "…"
        return f"{flag} {short}"

    def _is_champion_path(round_idx, slot_idx):
        """Check if this slot is on the champion's winning path."""
        if not champion:
            return False
        # Check if this slot's team eventually becomes champion
        if round_idx == 4:
            return all_rounds[4][0] == champion
        team = all_rounds[round_idx][slot_idx] if slot_idx < len(all_rounds[round_idx]) else None
        if not team or team != champion:
            # Check if champion passed through this slot
            return False
        return True

    # Calculate Y positions for each round
    def get_y_positions(count):
        total_h = H - 2 * TOP_PAD
        spacing = total_h / count
        return [TOP_PAD + spacing * i + spacing / 2 - NODE_H / 2 for i in range(count)]

    round_y_positions = [get_y_positions(c) for c in round_counts]

    # Build SVG
    elements = []
    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'style="width:100%; height:auto; max-height:600px; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">'
    )

    # Background
    elements.append(
        f'<rect width="{W}" height="{H}" rx="14" fill="rgba(17,86,117,0.15)"/>'
    )

    # Draw round labels
    for r_idx, label in enumerate(round_labels):
        x = LEFT_PAD + r_idx * ROUND_GAP + NODE_W / 2
        elements.append(
            f'<text x="{x}" y="{TOP_PAD - 1}" text-anchor="middle" '
            f'font-size="10" font-weight="700" fill="#29B5E8" opacity="0.8">{label}</text>'
        )

    # Draw nodes and connecting lines
    for r_idx in range(len(round_counts)):
        count = round_counts[r_idx]
        x = LEFT_PAD + r_idx * ROUND_GAP
        y_positions = round_y_positions[r_idx]
        teams_in_round = all_rounds[r_idx]

        for slot_idx in range(count):
            y = y_positions[slot_idx]
            team = teams_in_round[slot_idx] if slot_idx < len(teams_in_round) else None
            is_champ_path = _is_champion_path(r_idx, slot_idx)

            # Node rectangle
            fill = "#115675" if team else "rgba(17,86,117,0.4)"
            stroke = "#FFD700" if is_champ_path else "rgba(41,181,232,0.4)"
            stroke_w = "2" if is_champ_path else "1"

            elements.append(
                f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
                f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"/>'
            )

            # Team text
            label = _label(team)
            text_color = "#FFD700" if (r_idx == 4 and team) else ("#ffffff" if team else "#999999")
            font_size = "10" if len(label) > 14 else "11"
            elements.append(
                f'<text x="{x + NODE_W/2}" y="{y + NODE_H/2 + 4}" text-anchor="middle" '
                f'font-size="{font_size}" font-weight="600" fill="{text_color}">{label}</text>'
            )

            # Connecting line to next round
            if r_idx < len(round_counts) - 1:
                next_slot = slot_idx // 2
                next_x = LEFT_PAD + (r_idx + 1) * ROUND_GAP
                next_y_positions = round_y_positions[r_idx + 1]
                next_y = next_y_positions[next_slot] + NODE_H / 2

                # Line from right edge of current node to left edge of next node
                start_x = x + NODE_W
                start_y = y + NODE_H / 2
                mid_x = start_x + (next_x - start_x) / 2

                line_color = "#FFD700" if is_champ_path else "rgba(41,181,232,0.3)"
                line_w = "2" if is_champ_path else "1"

                # Elbow connector: horizontal out, vertical to align, horizontal in
                elements.append(
                    f'<path d="M {start_x} {start_y} L {mid_x} {start_y} '
                    f'L {mid_x} {next_y} L {next_x} {next_y}" '
                    f'fill="none" stroke="{line_color}" stroke-width="{line_w}"/>'
                )

    # Champion trophy at far right
    if champion:
        final_x = LEFT_PAD + 4 * ROUND_GAP
        final_y = round_y_positions[4][0]
        elements.append(
            f'<text x="{final_x + NODE_W + 15}" y="{final_y + NODE_H/2 + 5}" '
            f'font-size="20">🏆</text>'
        )

    elements.append("</svg>")
    return "\n".join(elements)
