# -*- coding: utf-8 -*-
from __future__ import division
from django.core.paginator import Paginator


class MyPaginator(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, range=5):
        super(MyPaginator, self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.range = range
        self.pages = []
        self.first_page = False
        self.last_page = False

    def paginated_ranges(self, page):
        left = page - self.range
        right = page + self.range
        if left < 1:
            left = 1
        if right > self.num_pages:
            right = self.num_pages
        self.pages = range(left, right + 1)
        self.first_page = True if left > 1 else False
        self.last_page = True if right < self.num_pages else False
        self.ellipsis_left = left - 1
        self.ellipsis_right = right + 1

