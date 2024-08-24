"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from django.urls import re_path
from storageadmin.views import DiskListView, DiskDetailView, DiskSMARTDetailView

disk_regex = "[A-Za-z0-9]+[A-Za-z0-9:_-]*"

urlpatterns = [
    re_path(r"^smart/(?P<command>.+)/(?P<did>\d+)$", DiskSMARTDetailView.as_view()),
    re_path(r"^(?P<command>scan)$", DiskListView.as_view()),
    re_path(r"^(?P<did>\d+)$", DiskDetailView.as_view()),
    re_path(r"^(?P<did>\d+)/(?P<command>.+)$", DiskDetailView.as_view()),
]
