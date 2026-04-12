from app.services.extraction import extract_job_capture, html_to_text


def test_html_to_text_strips_script_style_and_whitespace() -> None:
    text = html_to_text(
        """
        <html>
          <head><style>.x { color: red; }</style><script>alert("x")</script></head>
          <body><h1>Role</h1><p>Own   the roadmap.</p></body>
        </html>
        """
    )

    assert text == "Role Own the roadmap."


def test_extract_job_capture_prefers_submitted_fields_over_jsonld() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": "JSON-LD role",
            "hiringOrganization": {"name": "JSON-LD Co"},
            "jobLocation": {
              "@type": "Place",
              "address": {
                "addressLocality": "London",
                "addressCountry": "GB"
              }
            },
            "url": "/apply",
            "description": "<p>JSON-LD description.</p>"
          }
        </script>
      </head>
      <body>Fallback body text.</body>
    </html>
    """

    extracted = extract_job_capture(
        source_url="https://jobs.example.com/role",
        title="Submitted role",
        company="Submitted Co",
        raw_html=html,
    )

    assert extracted.title == "Submitted role"
    assert extracted.company == "Submitted Co"
    assert extracted.location == "London, GB"
    assert extracted.apply_url == "https://jobs.example.com/apply"
    assert extracted.description == "JSON-LD description."
    assert extracted.confidence == "medium"
    assert extracted.warnings == []


def test_extract_job_capture_handles_graph_jsonld() -> None:
    html = """
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@graph": [
          {"@type": "Organization", "name": "Not the job"},
          {
            "@type": ["Thing", "JobPosting"],
            "title": "Graph role",
            "hiringOrganization": "Graph Co",
            "description": "Graph description."
          }
        ]
      }
    </script>
    """

    extracted = extract_job_capture(raw_html=html)

    assert extracted.title == "Graph role"
    assert extracted.company == "Graph Co"
    assert extracted.description == "Graph description."
    assert extracted.confidence == "medium"


def test_extract_job_capture_falls_back_to_selected_text_and_warns() -> None:
    extracted = extract_job_capture(selected_text="Selected job text.")

    assert extracted.title is None
    assert extracted.description == "Selected job text."
    assert extracted.confidence == "low"
    assert extracted.warnings == ["No title extracted."]


def test_extract_job_capture_records_invalid_jsonld_warning_and_body_fallback() -> None:
    html = """
    <script type="application/ld+json">{bad json</script>
    <main>Fallback description text.</main>
    """

    extracted = extract_job_capture(title="Fallback role", raw_html=html)

    assert extracted.title == "Fallback role"
    assert extracted.description == "Fallback description text."
    assert extracted.warnings == ["Ignored invalid JSON-LD block."]
