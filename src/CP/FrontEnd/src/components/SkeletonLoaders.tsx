import { makeStyles, shorthands, tokens, Skeleton, SkeletonItem } from '@fluentui/react-components'

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalM),
    width: '100%'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.gap(tokens.spacingHorizontalM),
    flexWrap: 'wrap'
  },
  card: {
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalL),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.border('1px', 'solid', tokens.colorNeutralStroke2),
  },
  cardHeader: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalS)
  },
  cardContent: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalM),
    marginTop: tokens.spacingVerticalL
  },
  row: {
    display: 'flex',
    ...shorthands.gap(tokens.spacingHorizontalM),
    alignItems: 'center'
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalS)
  },
  formField: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap(tokens.spacingVerticalXS)
  }
})

interface PageSkeletonProps {
  variant?: 'list' | 'detail' | 'form'
}

export function PageSkeleton({ variant = 'list' }: PageSkeletonProps) {
  const styles = useStyles()
  
  return (
    <div className={styles.container}>
      {/* Page header with title and button */}
      <div className={styles.header}>
        <Skeleton>
          <SkeletonItem size={32} style={{ width: '200px' }} />
        </Skeleton>
        <Skeleton>
          <SkeletonItem size={32} style={{ width: '140px' }} />
        </Skeleton>
      </div>
      
      {variant === 'list' && <ListSkeleton />}
      {variant === 'detail' && <DetailSkeleton />}
      {variant === 'form' && <FormSkeleton />}
    </div>
  )
}

function ListSkeleton() {
  const styles = useStyles()
  
  return (
    <div className={styles.card}>
      <div className={styles.section}>
        {[1, 2, 3].map((i) => (
          <div key={i} className={styles.row}>
            <Skeleton>
              <SkeletonItem shape="circle" size={40} />
            </Skeleton>
            <div style={{ flex: 1 }}>
              <Skeleton>
                <SkeletonItem size={16} style={{ width: '60%' }} />
              </Skeleton>
              <Skeleton style={{ marginTop: '4px' }}>
                <SkeletonItem size={12} style={{ width: '40%' }} />
              </Skeleton>
            </div>
            <Skeleton>
              <SkeletonItem size={24} style={{ width: '80px' }} />
            </Skeleton>
          </div>
        ))}
      </div>
    </div>
  )
}

function DetailSkeleton() {
  const styles = useStyles()
  
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.row}>
          <Skeleton>
            <SkeletonItem shape="circle" size={48} />
          </Skeleton>
          <div style={{ flex: 1 }}>
            <Skeleton>
              <SkeletonItem size={24} style={{ width: '40%' }} />
            </Skeleton>
            <Skeleton style={{ marginTop: '8px' }}>
              <SkeletonItem style={{ width: '30%', height: '14px' }} />
            </Skeleton>
          </div>
          <Skeleton>
            <SkeletonItem size={28} style={{ width: '100px' }} />
          </Skeleton>
        </div>
      </div>
      
      <div className={styles.cardContent}>
        <Skeleton>
          <SkeletonItem size={16} style={{ width: '50%' }} />
        </Skeleton>
        <Skeleton>
          <SkeletonItem style={{ width: '65%', height: '14px' }} />
        </Skeleton>
        <Skeleton>
          <SkeletonItem style={{ width: '55%', height: '14px' }} />
        </Skeleton>
        
        <div className={styles.row}>
          <Skeleton>
            <SkeletonItem size={32} style={{ width: '100px' }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem size={32} style={{ width: '100px' }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem size={32} style={{ width: '100px' }} />
          </Skeleton>
        </div>
      </div>
    </div>
  )
}

function FormSkeleton() {
  const styles = useStyles()
  
  return (
    <div className={styles.card}>
      <div className={styles.section}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className={styles.formField}>
            <Skeleton>
              <SkeletonItem style={{ width: '120px', height: '14px' }} />
            </Skeleton>
            <Skeleton>
              <SkeletonItem size={36} style={{ width: '100%' }} />
            </Skeleton>
          </div>
        ))}
        
        <div className={styles.row} style={{ marginTop: tokens.spacingVerticalM }}>
          <Skeleton>
            <SkeletonItem size={32} style={{ width: '100px' }} />
          </Skeleton>
          <Skeleton>
            <SkeletonItem size={32} style={{ width: '100px' }} />
          </Skeleton>
        </div>
      </div>
    </div>
  )
}

interface CardSkeletonProps {
  rows?: number
}

export function CardSkeleton({ rows = 3 }: CardSkeletonProps) {
  const styles = useStyles()
  
  return (
    <div className={styles.card}>
      <div className={styles.section}>
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i}>
            <SkeletonItem size={16} style={{ width: `${60 + (i % 3) * 10}%` }} />
          </Skeleton>
        ))}
      </div>
    </div>
  )
}

interface ListItemSkeletonProps {
  count?: number
}

export function ListItemSkeleton({ count = 3 }: ListItemSkeletonProps) {
  const styles = useStyles()
  
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={styles.row} style={{ padding: tokens.spacingVerticalS }}>
          <Skeleton>
            <SkeletonItem shape="circle" size={40} />
          </Skeleton>
          <div style={{ flex: 1 }}>
            <Skeleton>
              <SkeletonItem size={16} style={{ width: '60%' }} />
            </Skeleton>
            <Skeleton style={{ marginTop: '4px' }}>
              <SkeletonItem size={12} style={{ width: '40%' }} />
            </Skeleton>
          </div>
          <Skeleton>
            <SkeletonItem size={24} style={{ width: '80px' }} />
          </Skeleton>
        </div>
      ))}
    </>
  )
}
