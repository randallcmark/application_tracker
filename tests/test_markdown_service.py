from app.services.markdown import render_markdown_blocks


def test_render_markdown_blocks_escapes_unsafe_html() -> None:
    rendered = render_markdown_blocks("### Heading\n* <script>alert(1)</script>", class_name="ai-markdown")

    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert "<h4>Heading</h4>" in rendered


def test_render_markdown_blocks_supports_basic_emphasis_and_lists() -> None:
    rendered = render_markdown_blocks(
        "Intro with **bold** and *italics*\n\n- First item\n- Second item",
        class_name="description-markdown",
    )

    assert '<div class="description-markdown">' in rendered
    assert "<strong>bold</strong>" in rendered
    assert "<em>italics</em>" in rendered
    assert "<ul><li>First item</li><li>Second item</li></ul>" in rendered


def test_render_markdown_blocks_escapes_class_name() -> None:
    rendered = render_markdown_blocks("Plain text", class_name='ai-markdown" onclick="alert(1)')

    assert '" onclick="' not in rendered
    assert 'class="ai-markdown&quot; onclick=&quot;alert(1)"' in rendered
