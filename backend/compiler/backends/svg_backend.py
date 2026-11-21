import math
from .base import Backend


NODE_W = 90
NODE_H = 40
H_SPACING = 120
V_SPACING = 80
PADDING = 40


class SVGBackend(Backend):
    @property
    def name(self):
        return "SVG"

    def generate(self, cir, title="Circuit Diagram"):
        nodes_dict = dict(cir.nodes)
        edges = list(cir.edges)
        parts = cir.all_parts

        levels, positions = self._layout(nodes_dict, edges)
        width, height = self._compute_dimensions(levels, positions, parts)
        svg_elements = []
        svg_elements.append(self._render_defs())
        svg_elements.append(self._render_background(width, height))

        node_positions = {}
        for nid, data in nodes_dict.items():
            lvl = levels.get(nid, 0)
            idx = positions.get(nid, 0)
            x = PADDING + lvl * H_SPACING
            y = PADDING + idx * V_SPACING
            node_positions[nid] = (x, y)
            svg_elements.append(
                self._render_node(x, y, data["label"], data.get("type", "input"))
            )

        for src, tgt in edges:
            if src in node_positions and tgt in node_positions:
                svg_elements.append(
                    self._render_edge(node_positions[src], node_positions[tgt])
                )

        if parts:
            svg_elements.append(self._render_parts_table(parts, width, node_positions))

        svg_content = "\n".join(svg_elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
            f'<rect width="100%" height="100%" fill="#fff" />\n'
            f'<text x="{width//2}" y="24" text-anchor="middle" '
            f'font-family="sans-serif" font-size="16" font-weight="bold" fill="#333">'
            f'{self._xml_escape(title)}</text>\n'
            f'{svg_content}\n'
            f'</svg>'
        )

    def _layout(self, nodes_dict, edges):
        levels = {}
        for nid, data in nodes_dict.items():
            if data.get("type") == "input":
                levels[nid] = 0

        changed = True
        while changed:
            changed = False
            for src, tgt in edges:
                if src in levels and tgt not in levels:
                    levels[tgt] = levels[src] + 1
                    changed = True
                elif src in levels and tgt in levels and levels[tgt] <= levels[src]:
                    levels[tgt] = levels[src] + 1
                    changed = True

        for nid in nodes_dict:
            if nid not in levels:
                levels[nid] = 0

        by_level = {}
        for nid, lvl in levels.items():
            by_level.setdefault(lvl, []).append(nid)

        positions = {}
        for lvl, nodes in by_level.items():
            for i, nid in enumerate(nodes):
                positions[nid] = i

        return levels, positions

    def _compute_dimensions(self, levels, positions, parts):
        max_level = max(levels.values()) if levels else 0
        max_per_level = {}
        for nid, lvl in levels.items():
            max_per_level[lvl] = max(max_per_level.get(lvl, 0), positions.get(nid, 0) + 1)
        max_vertical = max(max_per_level.values()) if max_per_level else 1
        width = PADDING * 2 + (max_level + 1) * H_SPACING + NODE_W
        height = PADDING * 2 + max_vertical * V_SPACING + NODE_H
        if parts:
            height += 40 + len(parts) * 22
        return int(width), int(height)

    def _render_defs(self):
        return (
            '<defs>\n'
            '  <marker id="arrowhead" markerWidth="10" markerHeight="7" '
            'refX="10" refY="3.5" orient="auto">\n'
            '    <polygon points="0 0, 10 3.5, 0 7" fill="#666" />\n'
            '  </marker>\n'
            '</defs>'
        )

    def _render_background(self, width, height):
        return f'<rect width="{width}" height="{height}" fill="#f8f9fa" rx="8" />'

    def _render_node(self, x, y, label, ntype):
        cx = x + NODE_W // 2
        cy = y + NODE_H // 2
        color = self._node_color(ntype)
        shape = self._node_shape(x, y, ntype)
        return (
            f'<g>\n'
            f'  {shape}\n'
            f'  <text x="{cx}" y="{cy + 4}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="11" fill="#fff" '
            f'font-weight="bold">{self._xml_escape(label)}</text>\n'
            f'</g>'
        )

    def _node_color(self, ntype):
        return {
            "input": "#27ae60",
            "gate": "#2980b9",
            "output": "#e67e22",
        }.get(ntype, "#95a5a6")

    def _node_shape(self, x, y, ntype):
        if ntype == "input":
            return (
                f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
                f'rx="20" fill="{self._node_color(ntype)}" />'
            )
        elif ntype == "output":
            return (
                f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
                f'rx="6" fill="{self._node_color(ntype)}" />'
            )
        else:
            return (
                f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
                f'rx="4" fill="{self._node_color(ntype)}" />'
            )

    def _render_edge(self, src_pos, tgt_pos):
        x1 = src_pos[0] + NODE_W
        y1 = src_pos[1] + NODE_H // 2
        x2 = tgt_pos[0]
        y2 = tgt_pos[1] + NODE_H // 2
        cx = (x1 + x2) / 2
        dy = y2 - y1
        return (
            f'<path d="M {x1} {y1} Q {cx} {y1 + dy * 0.3} {cx} {(y1 + y2) / 2} '
            f'Q {cx} {y2 - dy * 0.3} {x2} {y2}" '
            f'fill="none" stroke="#666" stroke-width="1.5" '
            f'marker-end="url(#arrowhead)" />'
        )

    def _render_parts_table(self, parts, width, node_positions):
        top_y = max(
            (y + NODE_H for _, y in node_positions.values()),
            default=100
        ) + 30
        table_x = 20
        rows = [
            '<g font-family="monospace" font-size="11">',
            f'<text x="{table_x}" y="{top_y}" font-weight="bold" '
            f'font-size="13" font-family="sans-serif" fill="#333">'
            f'DNA Parts ({len(parts)})</text>',
        ]
        header_y = top_y + 22
        rows.append(
            f'<text x="{table_x}" y="{header_y}" font-weight="bold" fill="#555">'
            f'ID</text>'
        )
        rows.append(
            f'<text x="{table_x + 150}" y="{header_y}" font-weight="bold" fill="#555">'
            f'Role</text>'
        )
        rows.append(
            f'<text x="{table_x + 250}" y="{header_y}" font-weight="bold" fill="#555">'
            f'Description</text>'
        )
        line_y = header_y + 4
        rows.append(
            f'<line x1="{table_x}" y1="{line_y}" x2="{width - 20}" y2="{line_y}" '
            f'stroke="#ddd" stroke-width="1" />'
        )
        for i, part in enumerate(parts):
            ry = header_y + 22 + i * 20
            pid = part.get("id", "")
            role = part.get("role", "")
            info = part.get("info", "")
            rows.append(
                f'<text x="{table_x}" y="{ry}" fill="#333">'
                f'{self._xml_escape(pid)}</text>'
            )
            rows.append(
                f'<text x="{table_x + 150}" y="{ry}" fill="#666">'
                f'{self._xml_escape(role)}</text>'
            )
            rows.append(
                f'<text x="{table_x + 250}" y="{ry}" fill="#888">'
                f'{self._xml_escape(info)}</text>'
            )
        rows.append("</g>")
        return "\n".join(rows)

    def generate_svg(self, cir, title="Circuit Diagram"):
        return self.generate(cir, title)

    @staticmethod
    def _xml_escape(text):
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
