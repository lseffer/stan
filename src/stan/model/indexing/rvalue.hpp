#ifndef STAN_MODEL_INDEXING_RVALUE_HPP
#define STAN_MODEL_INDEXING_RVALUE_HPP

#include <vector>
#include <Eigen/Dense>
#include <stan/model/indexing/index.hpp>
#include <stan/model/indexing/index_list.hpp>
#include <stan/model/indexing/rvalue_return.hpp>

namespace stan {
  namespace model {

    /**
     * Primary template structure for the rvalue indexer.
     * Specializations will implement a static function
     * <code>apply()</code> function mapping a container of type
     * <code>C</code> and index list of type <code>I</code> to the
     * result of applying the indexing.
     *
     * @tparam C type of container.
     * @tparam I index type list.
     */
    template <typename C, typename I>
    struct rvalue_indexer {
    };

    template <typename C>
    struct rvalue_indexer<C, nil_index_list> {
      static inline C apply(const C& c, const nil_index_list& /*idx*/) {
        return c;
      }
    };
    

    template <typename C, typename L>
    struct rvalue_indexer<C, cons_index_list<index_uni, L> > {
      typedef cons_index_list<index_uni, L> index_t;

      typedef typename rvalue_return<C, index_t>::type return_t;

      static inline return_t apply(const C& c, const index_t& idx) {
        return rvalue(c[idx.head_.n_], idx.tail_);
      }
    };

    template <typename C, typename T>
    struct rvalue_indexer<C, cons_index_list<index_multi, T> > {
      typedef cons_index_list<index_multi, T> index_t;

      typedef typename rvalue_return<C, index_t>::type return_t;
      
      static inline return_t apply(const C& c, const index_t& idx) {
        return_t result;
        for (size_t n = 0; n < idx.head_.ns_.size(); ++n)
          result.push_back(rvalue(c[idx.head_.ns_[n]], idx.tail_));
        return result;
      }
    };

    template <typename C, typename T>
    struct rvalue_indexer<C, cons_index_list<index_omni, T> > {
      typedef cons_index_list<index_omni, T> index_t;

      typedef typename rvalue_return<C, index_t>::type return_t;

      static inline return_t apply(const C& c, const index_t& idx) {
        return_t result;
        for (size_t n = 0; n < c.size(); ++n)
          result.push_back(rvalue(c[n], idx.tail_));
        return result;
      }
    };

    template <typename C, typename T>
    struct rvalue_indexer<C, cons_index_list<index_min, T> > {
      typedef cons_index_list<index_min, T> index_t;

      typedef typename rvalue_return<C, index_t>::type return_t;

      static inline return_t apply(const C& c, const index_t& idx) {
        return_t result;
        for (size_t n = idx.head_.min_; n < c.size(); ++n)
          result.push_back(rvalue(c[n], idx.tail_));
        return result;
      }
    };

    template <typename C, typename T>
    struct rvalue_indexer<C, cons_index_list<index_max, T> > {
      typedef cons_index_list<index_max, T> index_t;

      typedef typename rvalue_return<C, index_t>::type return_t;

      static inline return_t apply(const C& c, const index_t& idx) {
        return_t result;
        for (int n = 0; n <= idx.head_.max_; ++n)
          result.push_back(rvalue(c[n], idx.tail_));
        return result;
      }
    };

    template <typename C, typename T>
    struct rvalue_indexer<C, cons_index_list<index_min_max, T> > {
      typedef cons_index_list<index_min_max, T> index_t;

      typedef typename rvalue_return<C, index_t>::type return_t;

      static inline return_t apply(const C& c, const index_t& idx) {
        return_t result;
        for (int n = idx.head_.min_; n <= idx.head_.max_; ++n)
          result.push_back(rvalue(c[n], idx.tail_));
        return result;
      }
    };

    // mat[uni]
    template <typename T>
    struct rvalue_indexer<Eigen::Matrix<T, Eigen::Dynamic, Eigen::Dynamic>,
                          cons_index_list<index_uni, nil_index_list> > {
      static inline Eigen::Matrix<T, 1, Eigen::Dynamic> 
      apply(const Eigen::Matrix<T, Eigen::Dynamic, Eigen::Dynamic>& m,
            const cons_index_list<index_uni, nil_index_list>& idx) {
        return m.row(idx.head_.n_);
      }
    };

    // needs 52 implementations!  6 hrs at 10 minutes each!
    // mat[multi] : ns, omni, min, max, minmax
    // mat[uni,multi];
    // mat[multi,uni]
    // mat[multi,multi] :  (25 instances?)

    // vec[uni]
    // vec[multi]
    // rowvec[uni]
    // rowvec[multi]

    // 

    /**
     * Return the result of indexing the specified container
     * with the specified index list.
     *
     * <p>The return type reduces dimensions where the index
     * provides a single index.
     *
     * @tparam C type of container.
     * @tparam I type of index list.
     * @param[in] c container.
     * @param[in] idx index.
     * @return slice of container picked out by index.
     */
    template <typename C, typename I>
    inline typename rvalue_return<C, I>::type 
    rvalue(const C& c, const I& idx) {
      return rvalue_indexer<C, I>::apply(c, idx);
    }

  }
}
#endif
