import React, { Component } from 'react';
import { FormattedMessage, FormattedNumber } from 'react-intl';
import Truncate from 'react-truncate';

import Date from 'src/components/common/Date';
import Category from 'src/components/common/Category';
import Collection from 'src/components/common/Collection';

import './CollectionCard.css';

class CollectionCard extends Component {
  render() {
    const { collection } = this.props;
    if (!collection || !collection.id) {
      return (<span></span>)
    }
    return (
      <Collection.Link collection={collection} className="noLinkDecoration">
        <div className="CollectionCard pt-card pt-elevation-1 pt-interactive">
          <h4><Collection.Label collection={collection} /></h4>
          <div className="facts">
            <div className="fact">
              <Category collection={collection} />
            </div>
            <div className="fact">
              <FormattedMessage id="collection.total.count"
                                defaultMessage="{count} Entries"
                                values={{
                                  count: <FormattedNumber value={collection.count} />
                                }}/>
            </div>
          </div>
          {collection.summary &&
            <p>
              <Truncate lines={2}>
                { collection.summary }
              </Truncate>
            </p>
          }
          {!collection.summary &&
            (<p className="missing">
              <FormattedMessage id="collection.summary.missing" defaultMessage="This collection has no description."/>
            </p>)
          }
          <div className="bottom-fact">
            <i className="fa fa-fw fa-refresh" />
            <FormattedMessage id="collection.last_updated"
                              defaultMessage="Last updated: {date}"
                              values={{
                                date: <Date value={collection.updated_at} />
                              }}/>
          </div>
        </div>
      </Collection.Link>
    );
  }
}

export default CollectionCard;
