/*
 * libvirt-utils.h: misc helper APIs for python binding
 *
 * Copyright (C) 2013 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library.  If not, see
 * <http://www.gnu.org/licenses/>.
 *
 */

#ifndef __LIBVIRT_UTILS_H__
# define __LIBVIRT_UTILS_H__

# define STREQ(a,b) (strcmp(a,b) == 0)

# ifndef MIN
#  define MIN(a,b) (((a) < (b)) ? (a) : (b))
# endif

/* Return 1 if an array of N objects, each of size S, cannot exist due
   to size arithmetic overflow.  S must be positive and N must be
   nonnegative.  This is a macro, not a function, so that it
   works correctly even when SIZE_MAX < N.

   By gnulib convention, SIZE_MAX represents overflow in size
   calculations, so the conservative dividend to use here is
   SIZE_MAX - 1, since SIZE_MAX might represent an overflowed value.
   However, malloc (SIZE_MAX) fails on all known hosts where
   sizeof (ptrdiff_t) <= sizeof (size_t), so do not bother to test for
   exactly-SIZE_MAX allocations on such hosts; this avoids a test and
   branch when S is known to be 1.  */
# define xalloc_oversized(n, s) \
    ((size_t) (sizeof (ptrdiff_t) <= sizeof (size_t) ? -1 : -2) / (s) < (n))


/* The __attribute__((__warn_unused_result__)) feature
   is available in gcc versions 3.4 and newer,
   while the typeof feature has been available since 2.7 at least.  */
# if 3 < __GNUC__ + (4 <= __GNUC_MINOR__)
#  define ignore_value(x) \
    (__extension__ ({ __typeof__ (x) __x = (x); (void) __x; }))
# else
#  define ignore_value(x) ((void) (x))
# endif

# ifdef __GNUC__
/**
 * ATTRIBUTE_UNUSED:
 *
 * Macro to flag consciously unused parameters to functions
 */
#  ifndef ATTRIBUTE_UNUSED
#   define ATTRIBUTE_UNUSED __attribute__((__unused__))
#  endif

/* gcc's handling of attribute nonnull is less than stellar - it does
 * NOT improve diagnostics, and merely allows gcc to optimize away
 * null code checks even when the caller manages to pass null in spite
 * of the attribute, leading to weird crashes.  Coverity, on the other
 * hand, knows how to do better static analysis based on knowing
 * whether a parameter is nonnull.  Make this attribute conditional
 * based on whether we are compiling for real or for analysis, while
 * still requiring correct gcc syntax when it is turned off.  See also
 * http://gcc.gnu.org/bugzilla/show_bug.cgi?id=17308 */
#  ifndef ATTRIBUTE_NONNULL
#   if __GNUC_PREREQ (3, 3)
#    if STATIC_ANALYSIS
#     define ATTRIBUTE_NONNULL(m) __attribute__((__nonnull__(m)))
#    else
#     define ATTRIBUTE_NONNULL(m) __attribute__(())
#    endif
#   else
#    define ATTRIBUTE_NONNULL(m)
#   endif
#  endif

#  ifndef ATTRIBUTE_RETURN_CHECK
#   if __GNUC_PREREQ (3, 4)
#    define ATTRIBUTE_RETURN_CHECK __attribute__((__warn_unused_result__))
#   else
#    define ATTRIBUTE_RETURN_CHECK
#   endif
#  endif

# else
#  ifndef ATTRIBUTE_UNUSED
#   define ATTRIBUTE_UNUSED
#  endif
#  ifndef ATTRIBUTE_NONNULL
#   define ATTRIBUTE_NONNULL(m)
#  endif
#  ifndef ATTRIBUTE_RETURN_CHECK
#   define ATTRIBUTE_RETURN_CHECK
#  endif
# endif                         /* __GNUC__ */


#endif /* __LIBVIRT_UTILS_H__ */
