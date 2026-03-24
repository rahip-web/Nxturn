// C:\Users\Vinay\Project\frontend\src\stores\comment.ts
// --- FINAL, DEFINITIVE & CORRECTED VERSION ---

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { usePostsStore } from '@/stores/posts';

// --- Define Comment structure ---
export interface CommentAuthor {
  id: number;
  username: string;
  first_name: string;      
  last_name: string;       
  picture: string | null;
}

export interface Comment {
  id: number;
  author: CommentAuthor;
  content: string;
  created_at: string;
  updated_at: string;
  content_type_id: number;
  object_id: number;        
  parent: number | null;
  like_count: number;
  is_liked_by_user: boolean;
  comment_content_type_id: number;
}

// Define the store
export const useCommentStore = defineStore('comment', () => {
  const postsStore = usePostsStore();

  // --- State ---
  const commentsByPost = ref<Record<string, Comment[]>>({});
  const isLoading = ref(false);
  // --- THE FIX: Initialize with `null`, not a number ---
  const error = ref<string | null>(null);
  const isCreatingComment = ref(false);
  const createCommentError = ref<string | null>(null);

  // --- Actions ---
  async function fetchComments(postType: string, objectId: number) {
    const postKey = `${postType}_${objectId}`;
    isLoading.value = true;
    error.value = null;

    try {
      const apiUrl = `/comments/${postType}/${objectId}/`;
      const response = await axiosInstance.get<Comment[]>(apiUrl);

      if (Array.isArray(response.data)) {
          commentsByPost.value[postKey] = response.data;
      } else {
          console.error(`CommentStore: Received non-array data for comments ${postKey}:`, response.data);
          commentsByPost.value[postKey] = [];
      }
    } catch (err: any) {
      console.error(`CommentStore: Error fetching comments for ${postKey}:`, err);
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch comments.';
      delete commentsByPost.value[postKey];
    } finally {
      isLoading.value = false;
    }
  }

  async function createComment(
      postType: string, 
      objectId: number,
      content: string, 
      parentPostActualId: number,
      parentCommentId?: number
  ) {
    const postKey = `${postType}_${objectId}`;
    isCreatingComment.value = true;
    createCommentError.value = null;

    try {
      const apiUrl = `/comments/${postType}/${objectId}/`; 
      const payload: { content: string; parent?: number } = { content };
      if (parentCommentId) {
        payload.parent = parentCommentId;
      }
      
      const response = await axiosInstance.post<Comment>(apiUrl, payload);
      const newComment = response.data;

      if (!Array.isArray(commentsByPost.value[postKey])) {
        commentsByPost.value[postKey] = [];
      }
      commentsByPost.value[postKey].unshift(newComment);

      postsStore.incrementCommentCount(parentPostActualId); 

      return newComment;

    } catch (err: any) {
      console.error(`CommentStore: Error creating comment/reply for ${postKey}:`, err);
      createCommentError.value = err.response?.data?.detail || err.response?.data?.content?.[0] || 'Failed to post comment.';
      throw err; 
    } finally {
      isCreatingComment.value = false; 
    }
  }

  async function deleteComment(commentId: number, postType: string, objectId: number, parentPostId: number) {
    const postKey = `${postType}_${objectId}`;

    try {
      await axiosInstance.delete(`/comments/${commentId}/`);

      // Remove the deleted comment (and any direct replies) from the store
      if (commentsByPost.value[postKey]) {
        const beforeList = commentsByPost.value[postKey];
        const repliesToParent = beforeList.filter(c => c.parent === commentId);
        commentsByPost.value[postKey] = beforeList.filter(
          c => c.id !== commentId && c.parent !== commentId
        );

        // decrement the post-level comment count by number removed
        const totalRemoved = 1 + repliesToParent.length;
        postsStore.decrementCommentCount(parentPostId, totalRemoved);
      } else {
        postsStore.decrementCommentCount(parentPostId);
      }
      
      return true;

    } catch (err: any) {
      console.error(`CommentStore: Error deleting comment ID ${commentId}:`, err);
      throw err; 
    }
  }

  // --- NEW: Handle WebSocket signal for comment deletion ---
  function handleCommentDeletedSignal(commentId: number, postType: string, objectId: number) {
    const postKey = `${postType}_${objectId}`;
    console.log(`!!! COMMENT STORE DEBUG: handleCommentDeletedSignal called with commentId=${commentId}, postType=${postType}, objectId=${objectId}, postKey=${postKey}`);
    
    const existing = commentsByPost.value[postKey] || [];
    const removed = existing.find(c => c.id === commentId);

    commentsByPost.value[postKey] = existing.filter(c => c.id !== commentId);

    if (removed) {
      // update post-level comment count so top counter stays accurate
      postsStore.decrementCommentCount(objectId);
      console.log(`!!! COMMENT STORE DEBUG: Decremented post ${objectId} comment count due to deletion of ${commentId}`);
    }
  }
  // --- END OF NEW ---

  async function editComment(commentId: number, newContent: string, postType: string, objectId: number) {
    const postKey = `${postType}_${objectId}`;
    try {
      const apiUrl = `/comments/${commentId}/`; 
      const payload = { content: newContent };
      const response = await axiosInstance.put<Comment>(apiUrl, payload); 

      if (response.data && response.data.id) {
        if (commentsByPost.value[postKey]) {
          const commentIndex = commentsByPost.value[postKey].findIndex(c => c.id === commentId);
          if (commentIndex !== -1) {
            commentsByPost.value[postKey][commentIndex] = response.data;
          }
        }
        return response.data;
      } else {
        throw new Error("Comment edited, but received unexpected data from server.");
      }
    } catch (err: any) {
      console.error(`CommentStore: Error editing comment ID ${commentId}:`, err);
      throw err;
    }
  }

  async function toggleLikeOnComment(
    commentId: number,
    commentContentTypeId: number,
    parentPostType: string,
    parentObjectId: number
  ) {
    const postKey = `${parentPostType}_${parentObjectId}`;
    const commentsList = commentsByPost.value[postKey];
    if (!commentsList) return; 

    const commentIndex = commentsList.findIndex(c => c.id === commentId);
    if (commentIndex === -1) return; 

    try {
      const response = await axiosInstance.post<{ liked: boolean; like_count: number }>(
        `/content/${commentContentTypeId}/${commentId}/like/`
      );
      if (response.status === 200) {
        const { liked, like_count } = response.data;
        commentsByPost.value[postKey][commentIndex].is_liked_by_user = liked;
        commentsByPost.value[postKey][commentIndex].like_count = like_count;
      }
    } catch (error: any) {
      console.error('CommentStore: Error toggling like on comment API call:', error);
      throw error; 
    }
  }

  return {
    commentsByPost,
    isLoading,
    error,
    fetchComments,
    createComment,
    isCreatingComment,
    createCommentError,
    deleteComment,
    editComment,
    toggleLikeOnComment,
    handleCommentDeletedSignal,
  };
});