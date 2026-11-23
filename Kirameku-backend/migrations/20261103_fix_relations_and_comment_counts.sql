-- Align databases created by SQLModel with init_db.sql. Run with psql -v ON_ERROR_STOP=1.
BEGIN;

ALTER TABLE post DROP CONSTRAINT IF EXISTS post_category_id_fkey,
    ADD CONSTRAINT post_category_id_fkey FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL;
ALTER TABLE post_tag DROP CONSTRAINT IF EXISTS post_tag_post_id_fkey,
    ADD CONSTRAINT post_tag_post_id_fkey FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    DROP CONSTRAINT IF EXISTS post_tag_tag_id_fkey,
    ADD CONSTRAINT post_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE;
ALTER TABLE comment DROP CONSTRAINT IF EXISTS comment_post_id_fkey,
    ADD CONSTRAINT comment_post_id_fkey FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    DROP CONSTRAINT IF EXISTS comment_parent_id_fkey,
    ADD CONSTRAINT comment_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES comment(id) ON DELETE CASCADE,
    DROP CONSTRAINT IF EXISTS comment_github_user_id_fkey,
    ADD CONSTRAINT comment_github_user_id_fkey FOREIGN KEY (github_user_id) REFERENCES github_user(id) ON DELETE SET NULL;
ALTER TABLE message DROP CONSTRAINT IF EXISTS message_parent_id_fkey,
    ADD CONSTRAINT message_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES message(id) ON DELETE CASCADE,
    DROP CONSTRAINT IF EXISTS message_github_user_id_fkey,
    ADD CONSTRAINT message_github_user_id_fkey FOREIGN KEY (github_user_id) REFERENCES github_user(id) ON DELETE SET NULL;
ALTER TABLE chatter_comment DROP CONSTRAINT IF EXISTS chatter_comment_chatter_id_fkey,
    ADD CONSTRAINT chatter_comment_chatter_id_fkey FOREIGN KEY (chatter_id) REFERENCES chatter(id) ON DELETE CASCADE,
    DROP CONSTRAINT IF EXISTS chatter_comment_parent_id_fkey,
    ADD CONSTRAINT chatter_comment_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES chatter_comment(id) ON DELETE CASCADE,
    DROP CONSTRAINT IF EXISTS chatter_comment_github_user_id_fkey,
    ADD CONSTRAINT chatter_comment_github_user_id_fkey FOREIGN KEY (github_user_id) REFERENCES github_user(id) ON DELETE SET NULL;
ALTER TABLE photo DROP CONSTRAINT IF EXISTS photo_album_id_fkey,
    ADD CONSTRAINT photo_album_id_fkey FOREIGN KEY (album_id) REFERENCES album(id) ON DELETE CASCADE;
ALTER TABLE bookmark_site DROP CONSTRAINT IF EXISTS bookmark_site_category_id_fkey,
    ADD CONSTRAINT bookmark_site_category_id_fkey FOREIGN KEY (category_id) REFERENCES bookmark_category(id) ON DELETE CASCADE;

UPDATE chatter SET comments_count = (
    SELECT count(*) FROM chatter_comment
    WHERE chatter_comment.chatter_id = chatter.id AND chatter_comment.status = 'approved'
);

COMMIT;
