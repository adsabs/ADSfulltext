# ADS Full Text Extraction Pipeline Specification

## Bullet Points Aims

  1. Given a list of bibliographic codes their full text should be extracted
  1. Handle all relevant formats that can be given to it
  1. Solid framework with little intervention
  1. Easy to extend and build on top of
  1. Well documented

## Initial estimate (guestimate)

  1. Research, design, code review: `1 month` (including adsdata)
  1. Prototype (Python): `1 month` (`1 week` per queue)
  1. Prototype (Java): `2-4 weeks` (learning Java, Java TDD, and writing)
  1. Deployment (1 week)
  1. Documentation (1 week)

Total: 3 months and 2 week

## Time taken

  1. Research (estimate), 18 days
  1. Prototype (Python), v0.1, 38 days (including tests)
  1. Prototype (Java) prototype, v0.2, 21 days (including tests)
  1. Deployment 3 days
  1. Documentation (8.5)
    * coverage tests with web interface, 1 day
    * PEP8 style in all of the code including tests, 3 days
    * UTF-8 encoding throughout, 1.5 days
    * Written details, 3 days

Total: approximately 2 months and 29 days (assuming 30 day months)

## Overview of achievements

1. **DONE** Given a list of bibliographic codes their full text should be extracted

The pipeline checks the relevant bibliographic code it is given, checks if it is
to be extracted, and if yes it extracts the full text of the article.

1. **DONE** Handle all relevant formats that can be given to it

The pipeline works for the following formats:
  * HTML, HTTP, XML, text, OCR, and PDF

1. **DONE** Solid framework with little intervention

Both parts of the pipeline (Java and Python) daemonise themselves and are
managed by the supervisor daemon. The queuing of the packets is handled by
RabbitMQ, a piece of software designed specifically for this task. There is the
opportunity to have permanent store such that no there would be no loss of
messages even if RabbitMQ, however, this is not currently set. There are several
defaults in place that can be changed by the user, but should require no current
intervention other than starting/stopping the pipeline.

There are several tests in place:
  * Unit tests for the individual functions for both the Python and Java
workers.
  * Integration tests that check the behaviour between the Python/Java
  frameworks alongside the RabbitMQ instance.
  * Functionality tests that imitate the production stage of the application.
  This involves starting/stopping the application as if it were ever day usage,
  and supplying content as would be expected in every day usage.

Currently, the Unit and Integration tests give a coverage of ~86-88%, and is
probably slightly larger given some classes are not used in Java, but kept for
historical reasoning. Also, adding the functionality tests would also boost the
overall coverage.

1. **DONE** Easy to extend and build on top of

Settings templates are available for both of the pipelines (Java and Python)
that allow the relevant number of workers, the URIs of the RabbitMQ instances,
the names of queues, and many other options, to be altered without having to go
within the code base itself.

Each worker is on a separate queue, and each extractor function has been
separated in such a way that new ones can be easily implemented on the fly. For,
example, it took half a day to add an extra worker (ProxyPublisher), including
the relevant queues, binds, and exchanges, and also unit and integration tests.

If pull requests are made all of the tests are carried out by TravisCI (unit
and integration tests only) for both the Java and Python code bases. This allows
for reliable/robust changes to be applied to the production application.

Coverage of the tests is also included to ensure that if changes are made, then
also tests are included.

1. **DONE** Well documented

 * Time was spent to ensure that the Python code met PEP8 standards.
 * Reasons for the PDFExtractor used were documented
 * General explanation of development and deployment of the application have been
 included.
 * External applications, TavisCI and coveralls have been setup to allow
 the quality of the code to be quantified.
 * Waffle.io has been setup to ensure a transparent view of what issues exist,
 and how they are being taken care of within the team.
