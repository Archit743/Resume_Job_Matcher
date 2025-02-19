import io
from flask import Blueprint
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
resume_generator_module_bp = Blueprint("resume_generator_module_", __name__)

class ResumeGenerator:
    def __init__(self):
        self.model = ChatGroq(model="llama3-groq-70b-8192-tool-use-preview", 
                            api_key="{{ $API_KEY }}")
        self.parser = StrOutputParser()
        self.styles = self._create_styles()
    
    def _create_styles(self):
        styles = getSampleStyleSheet()
        
        # Add custom styles to the stylesheet
        styles.add(ParagraphStyle(
            name='NameStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a237e'),
            spaceBefore=15,
            spaceAfter=10,
            borderColor=colors.HexColor('#1a237e'),
            borderWidth=1,
            borderPadding=5,
            borderRadius=3
        ))
        
        styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Add custom style for skills
        custom_skill_style = ParagraphStyle(
            'SkillItem',  # Changed name from SkillsStyle to SkillItem
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=5,
            rightIndent=5,
            spaceAfter=3,
            bulletIndent=0,
            alignment=TA_LEFT
        )
        styles.add(custom_skill_style)
        
        return styles

    def _create_skills_section(self, skills):
        elements = []
        elements.append(Paragraph('Skills', self.styles['SectionHeading']))
        
        if isinstance(skills, list):
            skills_list = skills
        elif isinstance(skills, str):
            skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        else:
            return elements
        
        # Enhance skills with AI
        enhanced_skills = []
        for skill in skills_list:
            try:
                prompt = ChatPromptTemplate.from_template(
                    """Enhance the following skill description to be more professional and specific:
                    {skill}
                    
                    Return only the enhanced skill with no additional text."""
                )
                chain = prompt | self.model | self.parser
                enhanced_skill = chain.invoke({"skill": skill}).strip()
                enhanced_skills.append(enhanced_skill)
            except Exception as e:
                print(f"Error enhancing skill: {str(e)}")
                enhanced_skills.append(skill)
        
        # Create skills table with proper styling
        skills_data = []
        row = []
        for i, skill in enumerate(enhanced_skills):
            # Use the correct style name 'SkillItem'
            row.append(Paragraph(skill, self.styles['SkillItem']))
            if len(row) == 2 or i == len(enhanced_skills) - 1:
                while len(row) < 2:
                    row.append('')
                skills_data.append(row)
                row = []
        
        if skills_data:
            skills_table = Table(skills_data, colWidths=[3*inch, 3*inch])
            skills_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(skills_table)
        
        elements.append(Spacer(1, 10))
        return elements
    def enhance_bullet_points(self, text, role):
        prompt = ChatPromptTemplate.from_template(
            """Enhance the following bullet point for a {role} position to be more impactful and professional, 
            focusing on achievements and quantifiable results where possible:
            {text}
            
            Return only the enhanced bullet point with no additional text or formatting."""
        )
        chain = prompt | self.model | self.parser
        try:
            return chain.invoke({"role": role, "text": text}).strip()
        except Exception as e:
            print(f"Error enhancing bullet point: {str(e)}")
            return text
    
    def create_professional_pdf(self, resume_data):
        print("Received work experience data:", resume_data.get("work_experience", "No data found"))

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        
        # Header section
        elements.append(Paragraph(resume_data['personal_info']['name'], self.styles['NameStyle']))
        
        # Contact info
        contact_info = [
            resume_data['personal_info']['email'],
            resume_data['personal_info']['phone'],
            resume_data['personal_info']['location'],
            resume_data['personal_info'].get('linkedin', '')
        ]
        elements.append(Paragraph(' | '.join(filter(None, contact_info)), self.styles['ContactInfo']))
        
        # Enhanced summary
        elements.extend(self._create_summary_section(resume_data.get('summary', '')))
        
        # Experience Section
        elements.extend(self._create_experience_section(resume_data['work_experience']))
        
        # Education Section
        elements.extend(self._create_education_section(resume_data['education']))
        
        # Skills Section
        elements.extend(self._create_skills_section(resume_data['skills']))
        
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    def _create_summary_section(self, summary):
        elements = []
        summary_prompt = ChatPromptTemplate.from_template(
            """Enhance the following professional summary to be more impactful and compelling:
            {summary}
            
            Return only the enhanced summary with no additional text."""
        )
        summary_chain = summary_prompt | self.model | self.parser
        try:
            enhanced_summary = summary_chain.invoke({"summary": summary})
            elements.append(Paragraph('Professional Summary', self.styles['SectionHeading']))
            elements.append(Paragraph(enhanced_summary, self.styles['Normal']))
        except Exception as e:
            print(f"Error enhancing summary: {str(e)}")
            elements.append(Paragraph('Professional Summary', self.styles['SectionHeading']))
            elements.append(Paragraph(summary, self.styles['Normal']))
        return elements
    
    

    
    def _create_experience_section(self, experiences):
        elements = []
        elements.append(Paragraph('Professional Experience', self.styles['SectionHeading']))
        print("Creating experience section with data:", experiences)  # Debug print
        if isinstance(experiences, dict):
            num_experiences = len(experiences.get('company_name', []))
        
        for i in range(num_experiences):
            try:
                company = experiences['company_name'][i]
                position = experiences['position'][i]
                dates = experiences['work_dates'][i]
                description = experiences['work_description'][i]
                
                if not all([company, position, dates, description]):
                    print(f"Skipping incomplete experience entry {i}")  # Debug print
                    continue
                
                # Create company and position header
                elements.append(Paragraph(f"<b>{position}</b>", self.styles['Normal']))
                elements.append(Paragraph(company, self.styles['Normal']))
                elements.append(Paragraph(dates, self.styles['Normal']))
                
                # Process description bullets
                description_lines = description.split('\n')
                bullets = []
                
                for line in description_lines:
                    if line.strip():
                        # Enhance each bullet point
                        enhanced_bullet = self.enhance_bullet_points(line.strip(), position)
                        bullets.append(ListItem(
                            Paragraph(enhanced_bullet, self.styles['Normal'])
                        ))
                
                if bullets:
                    elements.append(ListFlowable(
                        bullets,
                        bulletType='bullet',
                        leftIndent=20,
                        bulletFontSize=8,
                        bulletOffsetY=2
                    ))
                
                # Add spacing between experiences
                elements.append(Spacer(1, 15))
                
            except Exception as e:
                print(f"Error processing experience entry {i}: {str(e)}")  # Debug print
                continue
            return elements
            
    def _create_education_section(self, education):
        elements = []
        elements.append(Paragraph('Education', self.styles['SectionHeading']))
        
        # Handle the case where education might be a dict with arrays
        if isinstance(education, dict):
            # Zip the arrays together to create individual education entries
            for institution, degree, date, gpa in zip(
                education.get('institution', []),
                education.get('degree', []),
                education.get('education_dates', []),
                education.get('gpa', [])
            ):
                if not all([institution, degree]):  # Allow missing GPA
                    continue
                    
                edu_table_data = [
                    [Paragraph(f"<b>{degree}</b>", self.styles['Normal']),
                     Paragraph(date, self.styles['Normal'])],
                    [Paragraph(f"{institution}", self.styles['Normal']),
                     Paragraph(f"GPA: {gpa}" if gpa else "", self.styles['Normal'])]
                ]
                
                edu_table = Table(edu_table_data, colWidths=[4*inch, 2*inch])
                edu_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(edu_table)
                elements.append(Spacer(1, 10))
        
        return elements