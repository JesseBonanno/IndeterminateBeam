"""Report generation for statically determinate beams.

Generates a step-by-step calculation report in LaTeX format, showing
equilibrium equations and reaction solutions. Optional figures (beam
schematic with reactions, internal force diagrams) are exported as PNG
if the kaleido package is installed. PDF output is optional (requires
a LaTeX distribution such as pdflatex on the system path).
"""

import subprocess
import sys
from pathlib import Path
from math import radians, sin

from sympy import latex, sympify


def _fmt_num(val):
    """Format number for LaTeX, avoiding scientific notation for typical engineering values."""
    v = float(val)
    if v == int(v):
        return str(int(v))
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _export_figure_to_png(fig, filepath, scale=2):
    """Export a Plotly figure to PNG. Returns True on success, False if export fails (e.g. kaleido not installed)."""
    try:
        fig.write_image(str(filepath), scale=scale)
        return True
    except Exception:
        return False


def _support_type_string(support):
    """Return a short LaTeX-friendly description of the support type."""
    fx, fy, fm = (bool(support._stiffness[i] != 0) for i in range(3))
    if fx and fy and fm:
        return "fixed"
    if fx and fy and not fm:
        return "pin"
    if not fx and fy and not fm:
        return "roller"
    if fm and (fx or fy):
        return "fixed"
    if fx and not fy:
        return "x-only"
    return "custom"


def _load_description(load, length_unit, force_unit, moment_unit, distributed_unit):
    """Return a short LaTeX-friendly description of the load, including total force for distributed loads."""
    from indeterminatebeam.loading import (
        PointLoad,
        PointTorque,
        UDL,
        DistributedLoad,
        TrapezoidalLoad,
    )

    if isinstance(load, PointTorque):
        return f"Point torque $M = {load.force:.4g}$ {moment_unit} at $x = {load.position}$ {length_unit}"
    if isinstance(load, PointLoad):
        return f"Point load $P = {load.force:.4g}$ {force_unit} at $x = {load.position}$ {length_unit}"
    if isinstance(load, UDL):
        a, b = load.span
        length = b - a
        total = load.force * length
        return (
            f"UDL $w = {load.force:.4g}$ {distributed_unit} from $x = {a}$ to $x = {b}$ {length_unit} "
            f"(length ${length:.4g}$ {length_unit}, total force $w \\times L = {load.force:.4g} \\times {length:.4g} = {total:.4g}$ {force_unit})"
        )
    if isinstance(load, TrapezoidalLoad):
        a, b = load.span
        f0, f1 = load.force
        length = b - a
        total = 0.5 * (f0 + f1) * length
        return (
            f"Trapezoidal load from $w_1 = {f0:.4g}$ to $w_2 = {f1:.4g}$ {distributed_unit} "
            f"from $x = {a}$ to $x = {b}$ {length_unit} "
            f"(length ${length:.4g}$ {length_unit}, total force $\\frac{{w_1+w_2}}{{2}} \\times L = {total:.4g}$ {force_unit})"
        )
    if isinstance(load, DistributedLoad):
        # Report generation only supports vertical loads (angle = 90 degrees)
        if load.angle != 90:
            raise ValueError(
                f"Report generation for DistributedLoad requires angle=90 (vertical). "
                f"Load has angle={load.angle}. "
                f"Non-vertical distributed loads are not supported in reports."
            )
        a, b = load.span
        length = b - a
        _dist_type, _w1, _w2, _total = _distributed_load_total(load)
        if _dist_type == "constant" and _w1 is not None:
            return (
                f"Distributed load $w = {_w1:.4g}$ {distributed_unit} from $x = {a}$ to $x = {b}$ {length_unit} "
                f"(length ${length:.4g}$ {length_unit}, total force $w \\times L = {_w1:.4g} \\times {length:.4g} = {_total:.4g}$ {force_unit})"
            )
        if _dist_type == "trapezoidal" and _w1 is not None and _w2 is not None:
            return (
                f"Distributed load from $w_1 = {_w1:.4g}$ to $w_2 = {_w2:.4g}$ {distributed_unit} "
                f"from $x = {a}$ to $x = {b}$ {length_unit} "
                f"(length ${length:.4g}$ {length_unit}, total force $\\frac{{w_1+w_2}}{{2}} \\times L = {_total:.4g}$ {force_unit})"
            )
        if _total is not None:
            return (
                f"Distributed load from $x = {a}$ to $x = {b}$ {length_unit} "
                f"(length ${length:.4g}$ {length_unit}, total force ${_total:.4g}$ {force_unit}, integrated)"
            )
        return f"Distributed load from $x = {a}$ to $x = {b}$ {length_unit} (length ${length:.4g}$ {length_unit})"
    return "Load"


def _distributed_load_total(load):
    """Determine distributed load type and total force. Returns (type, w1, w2, total).

    Supports UDL and TrapezoidalLoad types only.
    - For UDL: returns ("constant", force_value, None, total)
    - For TrapezoidalLoad: returns ("trapezoidal", w1, w2, total)
    - For other types: returns ("other", None, None, None)
    """
    from indeterminatebeam.loading import UDL, TrapezoidalLoad

    try:
        a, b = load.span
        length = b - a

        # Handle UDL (uniform/constant load)
        if isinstance(load, UDL):
            w_val = load.force
            total = w_val * length
            return ("constant", w_val, None, total)

        # Handle TrapezoidalLoad (linearly varying load)
        if isinstance(load, TrapezoidalLoad):
            w1, w2 = load.force
            total = 0.5 * (w1 + w2) * length
            return ("trapezoidal", w1, w2, total)

        # Unsupported load type
        return ("other", None, None, None)
    except Exception:
        return ("other", None, None, None)


def _build_equilibrium_term_lists(beam, unknowns, L_unit, F_unit, M_unit, D_unit):
    """Build explicit (description, value) terms for sum Fx, sum Fy and sum M in user units.

    Returns (fx_terms, fy_terms, m_terms). Each is a list of (latex_desc, value) where value
    is a float (load contribution) or a sympy symbol (reaction).
    """
    from math import cos
    from indeterminatebeam.loading import (
        PointLoad,
        PointTorque,
        UDL,
        DistributedLoad,
        TrapezoidalLoad,
    )

    fx_terms = []
    fy_terms = []
    m_terms = []

    for load in beam._loads:
        if isinstance(load, PointTorque):
            m_terms.append(
                (f"Point torque $M = {load.force:.4g}$ {M_unit}", load.force)
            )
            continue
        if isinstance(load, PointLoad):
            force_x = load.force * cos(radians(load.angle))
            force_y = load.force * sin(radians(load.angle))
            if abs(force_x) > 1e-10:
                fx_terms.append(
                    (
                        f"Point load $P_x = {load.force:.4g} \\cos({load.angle}\\degree)$ at $x = {load.position}$ {L_unit}",
                        force_x,
                    )
                )
            if abs(force_y) > 1e-10:
                fy_terms.append(
                    (
                        f"Point load $P = {load.force:.4g}$ {F_unit} at $x = {load.position}$ {L_unit}",
                        force_y,
                    )
                )
                m_terms.append(
                    (
                        f"Point load $P \\times x = {load.force:.4g} \\times {load.position}$ {M_unit}",
                        force_y * load.position,
                    )
                )
            continue
        if isinstance(load, UDL):
            a, b = load.span
            length = b - a
            angle = getattr(load, "angle", 90)
            force_y_udl = load.force * sin(radians(angle))
            force_x_udl = load.force * cos(radians(angle))
            total_f_y = force_y_udl * length
            total_f_x = force_x_udl * length
            if abs(total_f_x) > 1e-10:
                fx_terms.append(
                    (
                        f"UDL $w \\times L = {load.force:.4g} \\times {length:.4g}$ {F_unit} (horizontal component)",
                        total_f_x,
                    )
                )
            fy_terms.append(
                (
                    f"UDL $w \\times L = {load.force:.4g} \\times {length:.4g}$ {F_unit}",
                    total_f_y,
                )
            )
            centroid = a + length / 2
            m_terms.append(
                (
                    f"UDL resultant ${total_f_y:.4g} \\times {centroid:.4g}$ {M_unit}",
                    total_f_y * centroid,
                )
            )
            continue
        if isinstance(load, TrapezoidalLoad):
            a, b = load.span
            f0, f1 = load.force
            length = b - a
            angle = getattr(load, "angle", 90)
            total_f = 0.5 * (f0 + f1) * length * sin(radians(angle))
            total_f_x = 0.5 * (f0 + f1) * length * cos(radians(angle))
            if abs(total_f_x) > 1e-10:
                fx_terms.append(
                    (
                        f"Trapezoidal total (horizontal) $\\frac{{{f0:.4g}+{f1:.4g}}}{{2}} \\times {length:.4g}$ {F_unit}",
                        total_f_x,
                    )
                )
            fy_terms.append(
                (
                    f"Trapezoidal total $\\frac{{{f0:.4g}+{f1:.4g}}}{{2}} \\times {length:.4g}$ {F_unit}",
                    total_f,
                )
            )
            centroid = (
                a + length * (f0 + 2 * f1) / (3 * (f0 + f1))
                if (f0 + f1) != 0
                else a + length / 2
            )
            m_terms.append(
                (
                    f"Trapezoidal resultant ${total_f:.4g} \\times {centroid:.4g}$ {M_unit}",
                    total_f * centroid,
                )
            )
            continue
        if isinstance(load, DistributedLoad):
            # Report generation only supports vertical loads (angle = 90 degrees)
            if load.angle != 90:
                raise ValueError(
                    f"Report generation for DistributedLoad requires angle=90 (vertical). "
                    f"Load has angle={load.angle}. "
                    f"Non-vertical distributed loads are not supported in reports."
                )
            a, b = load.span
            length = b - a
            dist_type, w1, w2, total_f = _distributed_load_total(load)
            if total_f is None:
                try:
                    from sympy import integrate, N
                    from sympy.abc import x

                    total_f = float(N(integrate(load._y0, (x, a, b))))
                except Exception:
                    continue
            if dist_type == "constant" and w1 is not None:
                fy_terms.append(
                    (
                        f"Distributed load $w \\times L = {w1:.4g} \\times {length:.4g}$ {F_unit}",
                        total_f,
                    )
                )
            elif dist_type == "trapezoidal" and w1 is not None and w2 is not None:
                fy_terms.append(
                    (
                        f"Distributed load $\\frac{{w_1+w_2}}{{2}} \\times L = \\frac{{{w1:.4g}+{w2:.4g}}}{{2}} \\times {length:.4g}$ {F_unit}",
                        total_f,
                    )
                )
            else:
                fy_terms.append(
                    (
                        f"Distributed load total (integrated) ${_fmt_num(total_f)}$ {F_unit}",
                        total_f,
                    )
                )
            try:
                from sympy import integrate, N
                from sympy.abc import x

                mom = float(N(integrate(load._y0 * x, (x, a, b))))
                m_terms.append(
                    (f"Distributed load moment about 0 ${_fmt_num(mom)}$ {M_unit}", mom)
                )
            except Exception:
                pass
            continue

    for a in unknowns["x"]:
        pos = a["position"]
        var = a["variable"]
        fx_terms.append((f"$R_{{x,{pos}}}$ (reaction at $x = {pos}$ {L_unit})", var))

    for a in unknowns["y"]:
        pos = a["position"]
        var = a["variable"]
        fy_terms.append((f"$R_{{y,{pos}}}$ (reaction at $x = {pos}$ {L_unit})", var))
        m_terms.append((f"$R_{{y,{pos}}} \\times {pos}$ {M_unit}", var * pos))

    for a in unknowns["m"]:
        var = a["variable"]
        m_terms.append(
            (
                f"$M_{{{a['position']}}}$ (moment reaction at $x = {a['position']}$ {L_unit})",
                var,
            )
        )

    return fx_terms, fy_terms, m_terms


def _equation_line_by_line(
    terms, show_solution, reaction_values_dict, F_unit, M_unit, is_moment=False
):
    """Format terms as line-by-line LaTeX and optionally show solution for single unknown.

    terms: list of (desc, value) where value is float or sympy symbol.
    show_solution: if True and there is exactly one symbol in values, add solution line.
    reaction_values_dict: map symbol name (e.g. 'y_0') to numeric value for solution.
    Returns (lines_tex, full_equation_latex, single_solution_tex or None).
    """
    unit = M_unit if is_moment else F_unit
    lines = []
    total = sympify(0)
    symbols_in_eq = []
    for desc, val in terms:
        try:
            v = float(val)
            total = total + v
            lines.append(f"{desc} & $= {_fmt_num(v)}$ {unit} \\\\\\\\")
        except (TypeError, ValueError):
            total = total + val
            syms = val.free_symbols if hasattr(val, "free_symbols") else set()
            symbols_in_eq.extend(list(syms))
            lines.append(f"{desc} & ${latex(val)}$ \\\\\\\\")
    eq_latex = latex(total) + " = 0"
    lines_tex = "\n".join(lines)

    single_solution_tex = None
    if show_solution and symbols_in_eq:
        uniq = list(dict.fromkeys(symbols_in_eq))
        if len(uniq) == 1:
            sym = uniq[0]
            name = str(sym)
            if name in reaction_values_dict:
                val = reaction_values_dict[name]
                # Use force unit for x/y reactions, moment unit for m (moment) reactions
                sol_unit = M_unit if name.startswith("m_") else F_unit
                single_solution_tex = f"\\Rightarrow \\quad {latex(sym)} = {_fmt_num(val)} \\; \\text{{{sol_unit}}}"

    return lines_tex, eq_latex, single_solution_tex


def _write_latex_report(
    beam,
    fp,
    title="Determinate Beam Calculation Report",
    image_external=None,
    image_internal=None,
):
    """Write the full LaTeX report to an open file-like object.

    image_external : str or None
        Basename of the beam external figure (beam schematic + reaction forces) to include at top.
    image_internal : str or None
        Basename of the beam internal figure (shear, moment, deflection) to include at bottom.
    """
    if not beam.is_determinate():
        raise ValueError(
            "Report can only be generated for statically determinate beams. "
            "Use beam.is_determinate() to check."
        )
    if not getattr(beam, "_reactions", None) or not beam._reactions:
        raise ValueError(
            "Beam must be analysed before generating the report. Call beam.analyse() first."
        )

    F_Rx, F_Ry, M_R, reaction_vars, unknowns = beam._build_equilibrium_equations()
    L_unit = beam._units.get("length", "m")
    F_unit = beam._units.get("force", "N")
    M_unit = beam._units.get("moment", "N.m")
    D_unit = beam._units.get("distributed", "N/m")

    # Reaction values for single-unknown solution display (symbol name -> value)
    reaction_values_dict = {}
    for a in unknowns["x"]:
        pos = a["position"]
        if pos in beam._reactions:
            reaction_values_dict[str(a["variable"])] = beam._reactions[pos][0]
    for a in unknowns["y"]:
        pos = a["position"]
        if pos in beam._reactions:
            reaction_values_dict[str(a["variable"])] = beam._reactions[pos][1]
    for a in unknowns["m"]:
        pos = a["position"]
        if pos in beam._reactions:
            reaction_values_dict[str(a["variable"])] = beam._reactions[pos][2]

    # Build explicit line-by-line equilibrium terms
    fx_terms, fy_terms, m_terms = _build_equilibrium_term_lists(
        beam, unknowns, L_unit, F_unit, M_unit, D_unit
    )

    # Format each equation with line-by-line and optional single-unknown solution
    eq_x_lines, eq_x_full, eq_x_solution = _equation_line_by_line(
        fx_terms, True, reaction_values_dict, F_unit, M_unit, is_moment=False
    )
    eq_y_lines, eq_y_full, eq_y_solution = _equation_line_by_line(
        fy_terms, True, reaction_values_dict, F_unit, M_unit, is_moment=False
    )
    eq_m_lines, eq_m_full, eq_m_solution = _equation_line_by_line(
        m_terms, True, reaction_values_dict, F_unit, M_unit, is_moment=True
    )

    # Build list of support and load descriptions
    supports = sorted(beam._supports, key=lambda s: s._position)
    support_lines = []
    for s in supports:
        stype = _support_type_string(s)
        support_lines.append(f"    \\item {stype} at $x = {s._position}$ {L_unit}")

    load_lines = []
    for load in beam._loads:
        load_lines.append(
            "    \\item " + _load_description(load, L_unit, F_unit, M_unit, D_unit)
        )

    # Reaction solution table
    reaction_rows = []
    for pos in sorted(beam._reactions.keys()):
        rx, ry, rm = beam._reactions[pos]
        reaction_rows.append(
            f"{pos} {L_unit} & ${rx:.4g}$ {F_unit} & ${ry:.4g}$ {F_unit} & ${rm:.4g}$ {M_unit} \\\\\\\\"
        )

    supports_tex = "\n".join(support_lines) if support_lines else "    \\item (none)"
    loads_tex = "\n".join(load_lines) if load_lines else "    \\item (none)"
    reactions_tex = "\n".join(reaction_rows)

    # Equilibrium sections: line-by-line plus optional single-unknown solution
    def _eq_section(title, lines_tex, eq_full, solution_tex, eq_symbol):
        if not lines_tex.strip():
            return f"\\paragraph{{{title}}}\n\\[{eq_symbol} = 0 \\quad \\Rightarrow \\quad {eq_full}\\]"
        block = f"\\paragraph{{{title}}}\n"
        block += (
            "\\begin{center}\n\\begin{tabular}{@{}ll@{}}\n"
            + lines_tex
            + "\\end{tabular}\n\\end{center}\n"
        )
        block += f"\\[ {eq_symbol} = 0 \\quad \\Rightarrow \\quad {eq_full} \\]"
        if solution_tex:
            block += f"\n\\[{solution_tex}\\]"
        return block

    eq_x_section = _eq_section(
        "Sum of forces in $x$:",
        eq_x_lines,
        eq_x_full,
        eq_x_solution,
        "\\sum F_x",
    )
    eq_y_section = _eq_section(
        "Sum of forces in $y$:",
        eq_y_lines,
        eq_y_full,
        eq_y_solution,
        "\\sum F_y",
    )
    eq_m_section = _eq_section(
        "Sum of moments (about $x = 0$):",
        eq_m_lines,
        eq_m_full,
        eq_m_solution,
        "\\sum M_0",
    )

    # Optional figure blocks for LaTeX (empty if no images)
    if image_external:
        fig_external_tex = (
            r"""
\begin{figure}[ht]
\centering
\includegraphics[width=0.95\textwidth]{%s}
\caption{Beam schematic with applied loads and solved reaction forces.}
\end{figure}
"""
            % image_external
        )
    else:
        fig_external_tex = ""

    if image_internal:
        fig_internal_tex = (
            r"""
\begin{figure}[ht]
\centering
\includegraphics[width=0.95\textwidth]{%s}
\caption{Internal forces and deflection: normal force, shear force, bending moment, and deflection diagrams.}
\end{figure}
"""
            % image_internal
        )
    else:
        fig_internal_tex = ""

    doc = r"""
\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\usepackage{graphicx}
\geometry{margin=1in}

\title{%s}
\author{IndeterminateBeam}
\date{}

\begin{document}
\maketitle
%s

\section{Problem description}

\subsection{Beam}
Span length $L = %s$ %s.

\subsection{Supports}
\begin{itemize}
%s
\end{itemize}

\subsection{Loads}
\begin{itemize}
%s
\end{itemize}

\section{Equilibrium equations}

For a statically determinate beam, the three equations of equilibrium (in the plane) are sufficient to solve for the three reaction unknowns. Each equation is expanded explicitly below.

%s

%s

%s

\section{Solution}

Solving the linear system yields the following reactions:

\begin{center}
\begin{tabular}{|c|c|c|c|}
\hline
Support ($x$) & $R_x$ & $R_y$ & $M$ \\
\hline
%s
\hline
\end{tabular}
\end{center}
%s

\end{document}
""" % (
        title,
        fig_external_tex,
        float(beam._x1),
        L_unit,
        supports_tex,
        loads_tex,
        eq_x_section,
        eq_y_section,
        eq_m_section,
        reactions_tex,
        fig_internal_tex,
    )
    fp.write(doc)


def generate_determinate_report(
    beam,
    filename="beam_report",
    path=".",
    compile_pdf=True,
    title="Determinate Beam Calculation Report",
):
    """Generate a step-by-step calculation report for a statically determinate beam.

    The report is written in LaTeX and saved as a .tex file. Optionally,
    it can be compiled to PDF if a LaTeX distribution (e.g. pdflatex) is
    available on the system path.

    Parameters
    ----------
    beam : Beam
        The beam object. Must be statically determinate and already analysed
        (call beam.analyse() first).
    filename : str, optional
        Base name for the output file(s), without extension (default ``"beam_report"``).
    path : str or path-like, optional
        Directory in which to write the file(s). Default is the current working directory.
    compile_pdf : bool, optional
        If True, attempt to compile the .tex file to PDF using pdflatex (default False).
        Requires a LaTeX distribution (e.g. TeX Live, MiKTeX) on the system path.
    title : str, optional
        Title string for the report (default ``"Determinate Beam Calculation Report"``).

    Notes
    -----
    Solvability is checked by running the beam analysis: if the beam has not
    been analysed yet, :meth:`beam.analyse()` is called. If analysis fails
    (e.g. x loads but no x support, or y loads but insufficient y/m restraints),
    the resulting error is raised and no report is generated. Figures (beam
    schematic and internal diagrams) are included using the ``kaleido``
    package (a required dependency).

    Returns
    -------
    str
        Absolute path to the generated .tex file. If compile_pdf is True and
        compilation succeeds, the PDF is written to the same directory with
        the same base name.

    Raises
    ------
    ValueError
        If the beam is not statically determinate or cannot be solved (e.g.
        loads in a direction with no or insufficient supports).

    Examples
    --------
    >>> from indeterminatebeam import Beam, Support
    >>> from indeterminatebeam.loading import PointLoadV
    >>> from indeterminatebeam.report import generate_determinate_report
    >>> beam = Beam(6)
    >>> beam.add_supports(Support(0, (1, 1, 0)), Support(6, (0, 1, 0)))
    >>> beam.add_loads(PointLoadV(-15000, 3))
    >>> beam.analyse()
    >>> generate_determinate_report(beam, filename="example_report")
    '.../example_report.tex'
    >>> generate_determinate_report(beam, filename="example_report", compile_pdf=True)
    '.../example_report.tex'
    """
    # replace spaces in the filename with _ to prevent errors
    filename = filename.replace(" ", "_")

    if path is None:
        path = Path.cwd()
    else:
        path = Path(path)
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    tex_path = path / f"{filename}.tex"

    # Check solvability by solving: run analysis if not already done
    if not getattr(beam, "_reactions", None) or not beam._reactions:
        beam.analyse()

    # Generate and export figures (kaleido is a required dependency)
    image_external_basename = None
    image_internal_basename = None
    fig_external = beam.plot_beam_external()
    fig_internal = beam.plot_beam_internal()
    if _export_figure_to_png(fig_external, path / f"{filename}_beam_external.png"):
        image_external_basename = f"{filename}_beam_external.png"
    if _export_figure_to_png(fig_internal, path / f"{filename}_beam_internal.png"):
        image_internal_basename = f"{filename}_beam_internal.png"

    with open(tex_path, "w", encoding="utf-8") as f:
        _write_latex_report(
            beam,
            f,
            title=title,
            image_external=image_external_basename,
            image_internal=image_internal_basename,
        )

    if compile_pdf:
        try:
            subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    str(tex_path),
                ],
                cwd=str(path),
                check=True,
                capture_output=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            if isinstance(e, FileNotFoundError):
                sys.stderr.write(
                    "pdflatex not found. Install a LaTeX distribution (e.g. TeX Live, MiKTeX) "
                    "to compile the report to PDF. The .tex file was written successfully.\n"
                )
            else:
                sys.stderr.write(
                    f"pdflatex compilation failed. The .tex file was written to {tex_path}.\n"
                )

    return str(tex_path)
