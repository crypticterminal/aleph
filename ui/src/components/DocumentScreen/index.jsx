import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Helmet } from 'react-helmet';

import { fetchDocument } from 'src/actions';
import Screen from 'src/components/common/Screen';
import ScreenLoading from 'src/components/common/ScreenLoading';
import Breadcrumbs from 'src/components/common/Breadcrumbs';
import DualPane from 'src/components/common/DualPane';
import Entity from 'src/components/EntityScreen/Entity';
import DocumentInfo from './DocumentInfo';
import DocumentContent from './DocumentContent';

class DocumentScreen extends Component {
  componentDidMount() {
    const { documentId } = this.props;
    this.props.fetchDocument({ id: documentId });
  }

  componentDidUpdate(prevProps) {
    const { documentId } = this.props;
    if (documentId !== prevProps.documentId) {
      this.props.fetchDocument({ id: documentId });
    }
  }

  render() {
    const { document, location } = this.props;
    if (document === undefined || document.isFetching) {
      return <ScreenLoading />;
    }
    return (
      <Screen>
        <Helmet>
          <title>{document.title || document.file_name}</title>
        </Helmet>
        <Breadcrumbs collection={document.collection}>
          { document.parent && (
            <li>
              <Entity.Link entity={document.parent} className="pt-breadcrumb" icon truncate={30} />
            </li>
          )}
          <li>
            <Entity.Link entity={document} className="pt-breadcrumb" icon truncate={30} />
          </li>
        </Breadcrumbs>
        <DualPane>
          <DocumentInfo document={document} />
          <DocumentContent document={document} fragId={location.hash} />
        </DualPane>
      </Screen>
    );
  }
}

const mapStateToProps = (state, ownProps) => {
  const { documentId } = ownProps.match.params;
  const document = documentId !== undefined
    ? state.entities[documentId]
    : undefined;
  return { documentId, document };
}

export default connect(mapStateToProps, { fetchDocument })(DocumentScreen);
