Feature: Agentic Document Extraction and Visual Grounding

  As an enterprise user
  I want to extract structured data from various document types (e.g., PDFs, images)
  So that I can automate business workflows without building manual templates

  Background:
    Given the Document Extraction API is accessible
    And supported document types include PDF, PNG, and JPEG

  Scenario: Extract text, tables, and form fields from a multi-page PDF
    Given I upload a multi-page PDF document
    When the system parses the document
    Then it should identify and extract all text blocks
    And it should extract all tables with their rows and columns preserved
    And it should extract all form fields (including checkboxes)
    And each extracted element should include its page number and bounding box coordinates

  Scenario: Preserve hierarchical structure and relationships
    Given a document contains tables, images, and captions
    When the document is parsed
    Then the output JSON should maintain a parent-child structure
    And captions should be linked to their respective images or tables

  Scenario: Handle template-free and unseen layouts
    Given I upload a document with a layout never seen before
    When the system processes the document
    Then it should extract all relevant elements without requiring a pre-trained template
    And the extraction should maintain accuracy above 95%

  Scenario: Visual grounding for auditability
    Given a set of extracted elements
    When the output is generated
    Then each element should reference its exact page and bounding box in the document
    And the API should be able to provide a cropped image snippet for each grounding on request

  Scenario: Human-in-the-loop validation
    Given extracted results with confidence scores
    When a reviewer checks the extraction
    Then the system should display overlays on the document image corresponding to each extracted element
    And allow the reviewer to correct or validate the extracted values

  Scenario: Complex layouts and multi-column support
    Given a document with multi-column text and nested tables
    When the document is parsed
    Then all text and table structures should be preserved in reading order

  Scenario: Language and handwriting support
    Given a document with text in multiple languages or handwritten notes
    When the system parses the document
    Then it should attempt extraction using the appropriate OCR model
    And report which language(s) and OCR models were used for each page
