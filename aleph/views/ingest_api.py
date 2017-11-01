import os
import json
import shutil
from banal import is_mapping
from storagelayer import checksum
from flask import Blueprint, request
from tempfile import mkdtemp
from werkzeug.exceptions import BadRequest
from normality import safe_filename, stringify

from aleph.ingest import ingest_document
from aleph.model import Collection, Document
from aleph.views.serializers import DocumentSchema
from aleph.index.documents import index_document_id
from aleph.views.util import require, obj_or_404, jsonify, validate_data


blueprint = Blueprint('ingest_api', __name__)


def _load_parent(collection, meta):
    # Determine the parent document for the document that is to be
    # ingested. This can either be specified using a document ID,
    # or using a foreign ID (because the document ID may not be as
    # easily accessible to the client).
    if 'parent' not in meta:
        return
    data = meta.get('parent')
    parent = None
    if not is_mapping(data):
        parent = Document.by_id(data,
                                collection_id=collection.id)
    elif 'id' in data:
        parent = Document.by_id(data.get('id'),
                                collection_id=collection.id)
    elif 'foreign_id' in data:
        parent = Document.by_keys(collection=collection,
                                  foreign_id=data.get('foreign_id'))
    if parent is None:
        raise BadRequest(response=jsonify({
            'status': 'error',
            'message': 'Cannot load parent document'
        }, status=400))
    return parent.id


def _load_metadata():
    """Unpack the common, pre-defined metadata for all the uploaded files."""
    try:
        meta = json.loads(request.form.get('meta', '{}'))
    except Exception as ex:
        raise BadRequest(unicode(ex))

    validate_data(meta, DocumentSchema)
    foreign_id = stringify(meta.get('foreign_id'))

    # If a foreign_id is specified, we cannot upload multiple files at once.
    if len(request.files) > 1 and foreign_id is not None:
        raise BadRequest(response=jsonify({
            'status': 'error',
            'message': 'Multiple files with one foreign_id'
        }, status=400))

    if not len(request.files) and foreign_id is None:
        raise BadRequest(response=jsonify({
            'status': 'error',
            'message': 'Directories need to have a foreign_id'
        }, status=400))
    return meta, foreign_id


@blueprint.route('/api/2/collections/<int:id>/ingest', methods=['POST', 'PUT'])
def ingest_upload(id):
    collection = obj_or_404(Collection.by_id(id))
    require(request.authz.can_write(collection.id))
    meta, foreign_id = _load_metadata()
    parent_id = _load_parent(collection, meta)
    upload_dir = mkdtemp()
    try:
        documents = []
        for storage in request.files.values():
            path = safe_filename(storage.filename)
            path = os.path.join(upload_dir, path)
            storage.save(path)
            content_hash = checksum(path)
            document = Document.by_keys(collection=collection,
                                        parent_id=parent_id,
                                        foreign_id=foreign_id,
                                        content_hash=content_hash)
            document.mime_type = storage.mimetype
            document.file_name = storage.filename
            document.update(meta)
            ingest_document(document, path,
                            role_id=request.authz.id)
            documents.append(document)

        if not len(request.files):
            document = Document.by_keys(collection=collection,
                                        parent_id=parent_id,
                                        foreign_id=foreign_id)
            document.update(meta)
            ingest_document(document, upload_dir,
                            role_id=request.authz.id)
            documents.append(document)
    finally:
        shutil.rmtree(upload_dir)

    # Update child counts in index.
    if parent_id is not None:
        index_document_id.delay(parent_id)

    return jsonify({
        'status': 'ok',
        'documents': [DocumentSchema().dump(d).data for d in documents]
    })
