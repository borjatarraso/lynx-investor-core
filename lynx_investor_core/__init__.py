"""Lince Investor Suite — shared runtime for sector-specialized Lynx agents."""

from __future__ import annotations

__version__ = "5.3"

__author__ = "Borja Tarraso"
__author_email__ = "borja.tarraso@member.fsf.org"
__year__ = "2026"
__license__ = "BSD-3-Clause"

SUITE_NAME = "Lince Investor Suite"
SUITE_VERSION = "5.3"
SUITE_LABEL = f"{SUITE_NAME} v{SUITE_VERSION}"

LICENSE_NAME = "BSD 3-Clause License"
LICENSE_URL = "https://opensource.org/licenses/BSD-3-Clause"

LICENSE_TEXT = """\
BSD 3-Clause License

Copyright (c) 2026, Borja Tarraso <borja.tarraso@member.fsf.org>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "__year__",
    "__license__",
    "SUITE_NAME",
    "SUITE_VERSION",
    "SUITE_LABEL",
    "LICENSE_NAME",
    "LICENSE_URL",
    "LICENSE_TEXT",
]
