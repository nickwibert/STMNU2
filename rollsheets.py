import pandas as pd
import os
import calendar
from datetime import datetime
# ReportLab PDF generation
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, PageTemplate, NextPageTemplate, ListFlowable,\
                               Spacer, FrameBreak, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.lib import pagesizes, colors
from reportlab.platypus.paragraph import Paragraph
from functools import partial

from globals import QUERY_DIR, CURRENT_SESSION, PREVIOUS_SESSION


# Given a year, month, and day number (1=Monday, 2=Tuesday, ..., 6=Saturday),
# determine all the dates in that month which fall on the given day of the week,
# returned as a list of strings which represent the day only with a leading zero.
# For example, all the Mondays (day_num=1) in April 2025 would be returned as ['07', '14', '21', '28]
def get_dates_by_day_of_week(year, month, day_num):
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    days = []
    for week in cal.monthdatescalendar(year, month):
        if week[day_num].month == month:
            # Add leading zero
            if 0 <= week[day_num].day <= 9:
                days.append("0" + str(week[day_num].day))
            else:
                days.append(str(week[day_num].day))
    return days


# Draw title of rollsheet (class name) in appropriate location
def title(canvas, doc, class_name):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 18,)
    canvas.drawCentredString(doc.leftMargin + doc.width/2 - 50, doc.height + doc.bottomMargin - 30,
                             class_name)
    canvas.restoreState()


# Draw class info (instructor, classtime, session) in appropriate location
def top_right(canvas, doc, content):
    canvas.saveState()
    w, h = content.wrap(doc.width, doc.topMargin)
    content.drawOn(canvas, doc.width, doc.height)
    canvas.restoreState()


# Draw footer
def footer(canvas, doc, content):
    canvas.saveState()
    w, h = content.wrap(doc.width, doc.bottomMargin)
    content.drawOn(canvas, doc.leftMargin, h + 20)
    canvas.restoreState()


# Handle all information in header and footer together
def header_and_footer(canvas, doc, class_name, class_content, footer_content):
    title(canvas, doc, class_name)
    top_right(canvas, doc, class_content)
    footer(canvas, doc, footer_content)


# Function to generate class rollsheets given a database connection and set of class IDs.
# The generated rollsheets will be saved as a single PDF file.
def generate(conn, class_ids):
    # Set up Paragraph styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('header', parent=styles['Normal'], fontSize=16, leading=16*1.25))
    styles.add(ParagraphStyle('current roll', parent=styles['Normal'], fontSize=15, leading=15*1.74))
    styles.add(ParagraphStyle('previous roll', parent=styles['Normal'], fontSize=9, leading=9*1.74,
                            textColor=colors.mediumvioletred, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle('days', parent=styles['Normal'], fontSize=11, firstLineIndent=20, leading=11*1.5))
    styles.add(ParagraphStyle('trial', parent=styles['Normal'], fontSize=14, leading=14*1.65,
                            fontName='Helvetica-Bold'))
    # Name PDF file based on current session 
    filename = f"{calendar.month_abbr[CURRENT_SESSION.month].upper()}{CURRENT_SESSION.year}_ROLLSHEETS.pdf"

    # Set up document
    PAGESIZE = pagesizes.portrait(pagesizes.A4)
    pdf = BaseDocTemplate(filename, pagesize=PAGESIZE, 
            leftMargin = 1.5 * cm, 
            rightMargin = 2.2 * cm,
            topMargin = 1.5 * cm, 
            bottomMargin = 2.5 * cm)

    ### Create frames to organize rollsheet ###
    # frame1 will contain numbered list of students/slots in rollsheet
    frame1 = Frame(pdf.leftMargin,
                pdf.bottomMargin+pdf.height * (1/3),
                pdf.width * 2/3,
                pdf.height * (2/3),
                id='col1')
    # frame2 will contain the checkboxes for attendance
    frame2 = Frame(pdf.leftMargin+pdf.width*(2/3)-80,
                pdf.bottomMargin+pdf.height * (1/3),
                pdf.width * 1/3,
                pdf.height * (2/3),
                id='col2')
    # frame3 will contain the previous session's roll on the right hand side
    frame3 = Frame(pdf.leftMargin+pdf.width*(4/6) + 50,
                pdf.bottomMargin+pdf.height * (1/3),
                pdf.width * 1/3,
                pdf.height * (2/3),
                id='col3')
    # frame4 will take up the bottom third of the page, containing empty slots to enter trials
    frame4 = Frame(pdf.leftMargin + 20,
                pdf.bottomMargin,
                pdf.width,
                pdf.height * (1/3),
                id='col4')

    # List to hold Paragraphs, ListFlowables, etc. which is passed in to build PDF at end of loop
    Story = []

    # Load query to get class roll info
    with open(os.path.join(QUERY_DIR,'roll_info.sql'), 'r') as sql_file:
        sql_script = sql_file.read()    

    ### SPECIAL CASE: Need to create header/footer/PageTemplate once outside of loop,
    ### because of how 'NextPageTemplate' handler works
    class_info = pd.read_sql(f"SELECT * FROM classes WHERE CLASS_ID={class_ids[0]}", conn).squeeze()    
    header_content = Paragraph(f"{class_info['TEACH']}<br />{class_info['CLASSTIME']}<br />{class_info['SESSION']}", styles['header'])
    footer_content = Paragraph(datetime.now().strftime("Rollsheet printed on %m/%d/%Y at %I:%M %p"), styles['Normal'])
    template = PageTemplate(id=f'{class_ids[0]}', frames=[frame1,frame2,frame3,frame4],
                            onPage=partial(header_and_footer,
                            class_name=class_info['CLASSNAME'],
                            class_content=header_content,
                            footer_content=footer_content))
    pdf.addPageTemplates(template)


    # Generate roll sheet for each class in `class_ids`
    for i in range(len(class_ids)):
        class_id = int(class_ids[i])
        # Get current roll and be sure to only print the names of those who are paid
        current_roll = pd.read_sql(sql_script,
                                conn,
                                params={'class_id'      : class_id,
                                        'current_month' : CURRENT_SESSION.month,
                                        'current_year'  : CURRENT_SESSION.year})
        current_roll = current_roll.loc[current_roll['PAID']==1]

        # Get previous roll, including both those who were billed and those who paid for previous session
        previous_roll = pd.read_sql(sql_script,
                                conn,
                                params={'class_id'      : class_id,
                                        'current_month' : PREVIOUS_SESSION.month,
                                        'current_year'  : PREVIOUS_SESSION.year})
        previous_roll = previous_roll.loc[(previous_roll['PAID']==1) | (previous_roll['BILLED']==1)]

        # Create a list of Paragraphs to represent the class roll. Each Paragraph object will contain either a student's name,
        # or a blank slot (represented by a line where a name can be written in), and the number of elements in the list is 
        # deteremined by `class_info['MAX']`
        roll_slots = [Paragraph(f"{current_roll.loc[i,'FNAME']} {current_roll.loc[i,'LNAME']}", styles['current roll']) if i < current_roll.shape[0] \
                    else Paragraph('_'*25, styles['current roll']) \
                    for i in range(class_info['MAX'])]
        # Create ListFlowable to represent the names as a numbered list
        roll_list = ListFlowable(
                roll_slots,
                bulletType='1',
                bulletFormat='%s:',
                bulletFontSize=styles['current roll'].__getattribute__('fontSize'),
                leftIndent=30
            )
        
        # Add some blank space for alignment
        Story.append(Spacer(1,pdf.topMargin + 10))
        # Add roll list to document
        Story.append(roll_list)
        # Break to next frame
        Story.append(FrameBreak())

        # Create row of checkboxes as a drawing, `boxes` 
        boxes = Drawing(18*5,18)
        for box in range(5):
            boxes.add(Rect(0+(box*18), 0, 18, 18, fillColor=colors.white))  

        # Create ListFlowable of checkbox drawings, where each `boxes` drawing is a group of five boxes.
        # Again, the number of drawings rendered depends on `class_info['MAX']` so there are only as
        # many slots/checkboxes as there are spots in the class.
        box_list = ListFlowable(
                    [
                        [boxes, Spacer(1,8)]
                        for i in range(class_info['MAX'])
                    ],
                    bulletColor='white'
                )
                
        # Use custom function to get all the dates when this class will meet in the current session
        class_dates = get_dates_by_day_of_week(CURRENT_SESSION.year, CURRENT_SESSION.month, class_info['DAYOFWEEK'])

        # Add blank space for alignment, then the class dates to be displayed over the checkboxes
        Story.append(Spacer(1,pdf.topMargin-8))
        Story.append(Paragraph('&nbsp; '.join(class_dates), style=styles['days']))
        # Add the column of checkbox drawings
        Story.append(box_list)
        # Break to next frame
        Story.append(FrameBreak())

        # Get the roll for previous session, this time will be no blank slots to write in. If the previous session was not a full class,
        # we will simply print up to the last name without any blank spots / lines.
        prev_roll_slots = [Paragraph(f"{previous_roll.loc[i,'FNAME']} {previous_roll.loc[i,'LNAME']}", styles['previous roll']) \
                    for i in range(previous_roll.shape[0])]
        # Create ListFlowable to represent names as a numbered list
        prev_roll_list = ListFlowable(
                prev_roll_slots,
                bulletType='1',
                bulletFormat='%s:',
                bulletFontName=styles['previous roll'].__getattribute__('fontName'),
                bulletFontSize=styles['previous roll'].__getattribute__('fontSize'),
                bulletColor=styles['previous roll'].__getattribute__('textColor'),
                leftIndent=15
            )

        # Add blank space for alignment, then a header
        Story.append(Spacer(1,pdf.topMargin + 50))
        Story.append(Paragraph("PREVIOUS SESSION:", styles['previous roll']))
        # Add previous session's roll to document
        Story.append(prev_roll_list)
        # Break to next frame
        Story.append(FrameBreak())

        # Create `trial_list` as a set of 8 blank lines, all intended for write-in
        trial_list = ListFlowable(
                        [Paragraph('<u>TRIALS</u>' + '&nbsp;'*85 + '<u>DATE</u>',style=styles['trial']), Spacer(1,15)] +
                        [Paragraph('_'*54, style=styles['trial']) for i in range(8)],
                        bulletColor='white'
        )
        # Add trial section to document
        Story.append(trial_list)

        # If this is not the final page, we need to handle the template for the subsequent page
        if i < len(class_ids)-1:
            # Get class info for the next loop, create header_content
            class_info = pd.read_sql(f"SELECT * FROM classes WHERE CLASS_ID={class_ids[i+1]}", conn).squeeze()    
            header_content = Paragraph(f"{class_info['TEACH']}<br />{class_info['CLASSTIME']}<br />{class_info['SESSION']}", styles['header'])
            # Add new page template for the next loop
            pdf.addPageTemplates(PageTemplate(id=f'{class_ids[i+1]}', frames=[frame1,frame2,frame3,frame4],
                                            onPage=partial(header_and_footer,
                                            class_name=class_info['CLASSNAME'],
                                            class_content=header_content,
                                            footer_content=footer_content)))
            Story.append(NextPageTemplate(f'{class_ids[i+1]}'))
            # Break to next page before continuing to next class
            Story.append(PageBreak())

    # After all rollsheets have been generated, build PDF file
    pdf.build(Story)
    # Try to print PDF
    # os.startfile(filename, 'print')
