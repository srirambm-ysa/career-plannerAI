import os
from fpdf import FPDF
from app.models.assessment import Assessment


WINDOWS_FONTS = 'C:/Windows/Fonts'
_ARIAL = os.path.join(WINDOWS_FONTS, 'arial.ttf')
_ARIAL_BOLD = os.path.join(WINDOWS_FONTS, 'arialbd.ttf')
_HAS_ARIAL = os.path.isfile(_ARIAL) and os.path.isfile(_ARIAL_BOLD)


class RoadmapPDF(FPDF):
    _fn = 'Helvetica'

    def _f(self, style='', size=10):
        self.set_font(self._fn, style, size)

    def header(self):
        if self.page_no() > 1:
            self._f('', 7)
            self.set_text_color(148, 163, 184)
            self.cell(0, 6, 'Career AI Exposure Planner', align='R')
            self.ln(4)
            self.set_draw_color(226, 232, 240)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self._f('', 7)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')


def generate_assessment_pdf(assessment):
    return _build_pdf(assessment)


def render_pdf(assessment_id):
    from app import create_app
    _app = create_app()
    with _app.app_context():
        assessment = Assessment.query.get(assessment_id)
        if not assessment:
            return None
        return _build_pdf(assessment)


def _risk_color(score):
    if score is None:
        return (100, 100, 100)
    if score < 4:
        return (22, 101, 52)
    if score < 7:
        return (146, 64, 14)
    return (153, 27, 27)


def _risk_bg(score):
    if score is None:
        return (241, 245, 249)
    if score < 4:
        return (240, 253, 244)
    if score < 7:
        return (255, 251, 235)
    return (254, 242, 242)


def _build_pdf(assessment):
    pdf = RoadmapPDF()
    if _HAS_ARIAL:
        pdf.add_font('Arial', '', _ARIAL)
        pdf.add_font('Arial', 'B', _ARIAL_BOLD)
        pdf._fn = 'Arial'
    else:
        pdf._fn = 'Helvetica'

    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf._f('B', 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, 'Career AI Exposure Assessment', new_x='LMARGIN')
    pdf.ln(6)

    pdf._f('', 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, f"Candidate: {assessment.job_title or 'N/A'}   |   "
                    f"Industry: {assessment.industry or 'N/A'}   |   "
                    f"Experience: {assessment.years_exp or 0} yrs   |   "
                    f"Completed: {assessment.completed_at.strftime('%b %d, %Y') if assessment.completed_at else 'N/A'}")
    pdf.ln(10)

    tasks = list(assessment.tasks.all())
    scored = [t for t in tasks if t.risk_score is not None]

    if scored:
        avg = sum(t.risk_score for t in scored) / len(scored)
        pdf._f('B', 11)
        pdf.set_text_color(*_risk_color(avg))
        pdf.cell(0, 8, f"Average Risk Score: {avg:.1f} / 10")
        pdf.ln(10)

    pdf._f('B', 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, 'Task Risk Scores')
    pdf.ln(8)

    pdf.set_draw_color(203, 213, 225)
    pdf._f('B', 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(51, 65, 85)

    pdf.cell(14, 7, 'Score', border=1, fill=True, align='C')
    pdf.cell(126, 7, 'Task', border=1, fill=True)
    pdf.cell(50, 7, 'Category', border=1, fill=True, align='C')
    pdf.ln()

    pdf._f('', 8)
    for task in scored:
        score_color = _risk_color(task.risk_score)
        score_bg = _risk_bg(task.risk_score)

        pdf.set_fill_color(*score_bg)

        pdf.set_text_color(*score_color)
        pdf._f('B', 9)
        pdf.cell(14, 14, f'{task.risk_score:.0f}', border=1, fill=True, align='C')

        pdf.set_text_color(30, 41, 59)
        pdf._f('', 8)
        task_text = task.description
        expl_text = f"({task.explanation})" if task.explanation else ''
        x_before = pdf.get_x()
        y_before = pdf.get_y()
        pdf.multi_cell(126, 5, f"{task_text}\n{expl_text}", border=1, fill=True)
        y_after = pdf.get_y()
        row_h = max(y_after - y_before, 14)

        pdf.set_xy(x_before + 126, y_before)

        pdf._f('', 7)
        pdf.set_text_color(100, 116, 139)
        cat = task.category or ''
        pdf.cell(50, row_h, cat, border=1, fill=True, align='C')
        pdf.set_xy(10, y_before + row_h)

        if y_before + row_h > 270:
            pdf.add_page()

    pdf.ln(8)

    pdf._f('B', 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, 'Upskilling Roadmap')
    pdf.ln(8)

    roadmap_items = list(assessment.roadmap_items.all())
    if roadmap_items:
        pdf.set_draw_color(203, 213, 225)
        pdf._f('B', 8)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(51, 65, 85)

        pdf.cell(10, 7, '#', border=1, fill=True, align='C')
        pdf.cell(55, 7, 'Skill', border=1, fill=True)
        pdf.cell(20, 7, 'Timeline', border=1, fill=True, align='C')
        pdf.cell(25, 7, 'Category', border=1, fill=True, align='C')
        pdf.cell(80, 7, 'Description', border=1, fill=True)
        pdf.ln()

        pdf._f('', 8)
        for item in roadmap_items:
            priority_color = _risk_color(6 - item.priority + 1)
            timeline_colors = {
                'short': (22, 101, 52),
                'medium': (30, 64, 175),
                'long': (107, 33, 168),
            }
            tl_col = timeline_colors.get(item.timeline, (100, 116, 139))

            pdf.set_text_color(30, 41, 59)

            pdf._f('B', 9)
            pdf.set_text_color(*priority_color)
            pdf.cell(10, 12, str(item.priority), border=1, align='C')

            pdf.set_text_color(15, 23, 42)
            pdf._f('B', 8)
            pdf.cell(55, 12, item.skill_name[:40], border=1)

            pdf.set_text_color(*tl_col)
            pdf._f('', 7)
            pdf.cell(20, 12, item.timeline.capitalize() if item.timeline else '', border=1, align='C')

            pdf.set_text_color(100, 116, 139)
            pdf._f('', 7)
            pdf.cell(25, 12, item.category[:20] if item.category else '', border=1, align='C')

            pdf.set_text_color(71, 85, 105)
            desc = item.description[:80] if item.description else ''
            pdf.cell(80, 12, desc, border=1)
            pdf.ln()

        pdf.ln(4)

        for item in roadmap_items:
            if item.resources:
                pdf._f('', 7)
                pdf.set_text_color(59, 130, 246)
                res_list = item.resources if isinstance(item.resources, list) else []
                pdf.cell(0, 5, f"{item.skill_name[:30]} resources: {', '.join(res_list[:3])}",
                         new_x='LMARGIN')
                pdf.ln(4)
    else:
        pdf._f('', 9)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 8, 'No roadmap items available.')
        pdf.ln()

    pdf.ln(10)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf._f('', 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, 'Generated by Career AI Exposure Planner  |  Powered by OpenRouter AI',
             align='C', new_x='LMARGIN')

    return bytes(pdf.output())
